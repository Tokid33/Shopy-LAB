import json

from sqlalchemy.orm import Session

from app.models import AgentRun
from app.models.enums import AgentType
from app.schemas.agents import (
    ProductScoutRunRequest,
    ProductScoutRunResponse,
    ScoutCandidate,
    SupplierCheckRunRequest,
    SupplierCheckRunResponse,
    SupplierResult,
)
from app.schemas.hypothesis import ProductCardCreate
from app.services.agents.providers import (
    FakeLLMExtractor,
    FakeSearchProvider,
    FakeWebPageFetcher,
    LLMExtractor,
    SearchProvider,
    WebPageFetcher,
)
from app.services.agents.runtime import (
    add_artifact,
    add_decision_log,
    add_task,
    create_agent_run,
    mark_run_completed,
    mark_run_failed,
    mark_run_running,
)
from app.services.scoring import score_product
from app.services.unit_economics import UnitEconomicsInput, calculate_unit_economics


class ProductScoutAgentService:
    def __init__(
        self,
        db: Session,
        search_provider: SearchProvider | None = None,
        web_fetcher: WebPageFetcher | None = None,
        extractor: LLMExtractor | None = None,
    ):
        self.db = db
        self.search_provider = search_provider or FakeSearchProvider()
        self.web_fetcher = web_fetcher or FakeWebPageFetcher()
        self.extractor = extractor or FakeLLMExtractor()

    def run(self, payload: ProductScoutRunRequest) -> ProductScoutRunResponse:
        run = create_agent_run(self.db, AgentType.product_scout, payload.model_dump(), hypothesis_id=payload.cycle_id)
        try:
            mark_run_running(run)
            shortlist: list[ScoutCandidate] = []
            reserve: list[ScoutCandidate] = []
            reject: list[ScoutCandidate] = []

            for category in payload.categories:
                search_query = f"{payload.market} {category} winning products"
                results = self.search_provider.search(search_query, limit=payload.limit)
                add_task(self.db, run.id, "search", "completed", {"query": search_query}, {"result_count": len(results)})

                for item in results:
                    raw_text = self.web_fetcher.fetch(item["url"])
                    extracted = self.extractor.extract_product_candidate(raw_text)

                    card_payload = ProductCardCreate(
                        product_name=f"{extracted['product_name']} ({category})",
                        category=category,
                        cost_of_goods=extracted["cost_of_goods"],
                        target_price=extracted["target_price"],
                        shipping_cost=extracted["shipping_cost"],
                        problem_or_desire_score=extracted["problem_or_desire_score"],
                        visual_potential_score=extracted["visual_potential_score"],
                        margin_score=extracted["margin_score"],
                        ad_risk_score=extracted["ad_risk_score"],
                        logistics_risk_score=extracted["logistics_risk_score"],
                    )
                    scored = score_product(card_payload)
                    candidate = ScoutCandidate(
                        product_name=card_payload.product_name,
                        category=category,
                        total_score=scored.total_score,
                        decision=scored.decision,
                    )
                    if scored.decision == "shortlist":
                        shortlist.append(candidate)
                    elif scored.decision == "reserve":
                        reserve.append(candidate)
                    else:
                        reject.append(candidate)

                    add_decision_log(
                        self.db,
                        run.id,
                        candidate.product_name,
                        scored.decision,
                        scored.explanation,
                        score=scored.total_score,
                    )

            output = {
                "shortlist": [item.model_dump() for item in shortlist],
                "reserve": [item.model_dump() for item in reserve],
                "reject": [item.model_dump() for item in reject],
            }
            add_artifact(self.db, run.id, "product_scout_output", output)
            mark_run_completed(run, output)
            self.db.commit()
            self.db.refresh(run)

            return ProductScoutRunResponse(
                run_id=run.id,
                agent_type=run.agent_type.value,
                status=run.status.value,
                shortlist=shortlist,
                reserve=reserve,
                reject=reject,
            )
        except Exception as exc:
            mark_run_failed(run, str(exc))
            self.db.commit()
            raise


class SupplierCheckAgentService:
    def __init__(self, db: Session):
        self.db = db

    def run(self, payload: SupplierCheckRunRequest) -> SupplierCheckRunResponse:
        run = create_agent_run(self.db, AgentType.supplier_check, payload.model_dump(), hypothesis_id=payload.cycle_id)
        try:
            mark_run_running(run)
            results: list[SupplierResult] = []

            for item in payload.shortlist_items:
                economics = calculate_unit_economics(
                    UnitEconomicsInput(
                        cogs=item.cost_of_goods,
                        shipping_cost=item.shipping_cost,
                        ad_cost_per_order=12,
                        transaction_fee=1.8,
                        selling_price=item.target_price,
                    )
                )

                if economics.margin_percent >= 35:
                    supplier_status = "verified"
                    recommendation = "go_to_site"
                elif economics.margin_percent >= 20:
                    supplier_status = "needs_review"
                    recommendation = "reserve"
                else:
                    supplier_status = "high_risk"
                    recommendation = "fail"

                result = SupplierResult(
                    product_name=item.product_name,
                    supplier_status=supplier_status,
                    contribution_margin=economics.contribution_margin,
                    recommendation=recommendation,
                )
                results.append(result)
                add_decision_log(
                    self.db,
                    run.id,
                    item.product_name,
                    recommendation,
                    f"Margin percent {economics.margin_percent}",
                    score=economics.margin_percent,
                )

            recommendations = {r.recommendation for r in results}
            if "go_to_site" in recommendations:
                final_recommendation = "go_to_site"
            elif "reserve" in recommendations:
                final_recommendation = "reserve"
            else:
                final_recommendation = "fail"

            output = {
                "results": [r.model_dump() for r in results],
                "final_recommendation": final_recommendation,
            }
            add_task(self.db, run.id, "supplier_check", "completed", payload.model_dump(), output)
            add_artifact(self.db, run.id, "supplier_check_output", output)
            mark_run_completed(run, output)
            self.db.commit()
            self.db.refresh(run)

            return SupplierCheckRunResponse(
                run_id=run.id,
                agent_type=run.agent_type.value,
                status=run.status.value,
                results=results,
                final_recommendation=final_recommendation,
            )
        except Exception as exc:
            mark_run_failed(run, str(exc))
            self.db.commit()
            raise


def get_agent_run(db: Session, run_id: int) -> AgentRun | None:
    return db.get(AgentRun, run_id)


def parse_run_payload(run: AgentRun) -> dict:
    return {
        "run_id": run.id,
        "agent_type": run.agent_type.value,
        "status": run.status.value,
        "input_payload": json.loads(run.input_payload),
        "output_payload": json.loads(run.output_payload) if run.output_payload else None,
        "error_message": run.error_message,
    }
