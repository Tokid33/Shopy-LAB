import json
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.services.agents.prompts import load_prompt
from app.services.agents.providers import (
    LLMExtractor,
    SearchProvider,
    WebPageFetcher,
    get_fetch_provider,
    get_llm_extractor,
    get_search_provider,
    provider_snapshot,
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

ALLOWED_SIGNALS = {"green", "yellow", "red"}
ALLOWED_SUPPLIER_STATUSES = {"passed", "quick_check", "failed"}


class AgentExecutionError(ValueError):
    pass


class ProductScoutAgentService:
    def __init__(
        self,
        db: Session,
        mode: str | None = None,
        search_provider: SearchProvider | None = None,
        web_fetcher: WebPageFetcher | None = None,
        extractor: LLMExtractor | None = None,
    ):
        self.db = db
        self.mode = mode or settings.agent_mode
        self.search_provider = search_provider or get_search_provider(self.mode)
        self.web_fetcher = web_fetcher or get_fetch_provider(self.mode)
        self.extractor = extractor or get_llm_extractor(self.mode)

    def run(self, payload: ProductScoutRunRequest) -> ProductScoutRunResponse:
        trace_id = str(uuid.uuid4())
        prompt = load_prompt("product_scout")
        snapshot = provider_snapshot(self.mode)

        run = create_agent_run(
            self.db,
            AgentType.product_scout,
            payload.model_dump(),
            provider_snapshot=snapshot,
            trace_id=trace_id,
            hypothesis_id=payload.cycle_id,
            prompt_path=prompt["path"],
            prompt_version=prompt["version"],
        )
        warnings: list[str] = []
        try:
            mark_run_running(run)
            shortlist: list[ScoutCandidate] = []
            reserve: list[ScoutCandidate] = []
            reject: list[ScoutCandidate] = []
            seen_urls: set[str] = set()

            for category in payload.categories:
                search_query = f"{payload.market} {category} winning products"
                raw_results = self.search_provider.search(search_query, limit=min(payload.limit, settings.max_search_results))
                dedup_results = [item for item in raw_results if item.get("url") and not (item["url"] in seen_urls or seen_urls.add(item["url"]))]
                add_task(
                    self.db,
                    run.id,
                    "search",
                    "completed",
                    {"query": search_query},
                    {"raw_count": len(raw_results), "dedup_count": len(dedup_results)},
                )

                for item in dedup_results[: settings.max_fetch_pages]:
                    raw_text = self.web_fetcher.fetch(item["url"])
                    extracted = self.extractor.extract_product_candidate(raw_text, prompt=prompt["content"])

                    if settings.enable_raw_artifact_capture:
                        add_artifact(
                            self.db,
                            run.id,
                            "raw_product_extraction",
                            {"url": item["url"], "raw_text_preview": raw_text[:500], "extracted": extracted},
                            uri=item["url"],
                            provider_name=self.extractor.name,
                            prompt_path=prompt["path"],
                            trace_id=trace_id,
                        )

                    if not self._is_valid_product_extraction(extracted):
                        warnings.append(f"Invalid product extraction for url={item['url']}")
                        continue

                    card_payload = ProductCardCreate(
                        product_name=extracted["product_name"],
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

                    add_decision_log(self.db, run.id, candidate.product_name, scored.decision, scored.explanation, score=scored.total_score)

            if not shortlist and not reserve and not reject:
                raise AgentExecutionError("Product scout produced no valid candidates after quality gates")

            output = {
                "trace_id": trace_id,
                "shortlist": [item.model_dump() for item in shortlist],
                "reserve": [item.model_dump() for item in reserve],
                "reject": [item.model_dump() for item in reject],
                "warnings": warnings,
            }
            add_artifact(
                self.db,
                run.id,
                "product_scout_output",
                output,
                provider_name=self.search_provider.name,
                prompt_path=prompt["path"],
                trace_id=trace_id,
            )
            mark_run_completed(run, output, warnings=warnings)
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
            mark_run_failed(run, str(exc), warnings=warnings)
            self.db.commit()
            raise

    @staticmethod
    def _is_valid_product_extraction(extracted: dict) -> bool:
        required = [
            "product_name",
            "signal",
            "problem_or_desire_score",
            "visual_potential_score",
            "margin_score",
            "ad_risk_score",
            "logistics_risk_score",
            "cost_of_goods",
            "target_price",
            "shipping_cost",
        ]
        if any(field not in extracted for field in required):
            return False
        if not extracted["product_name"]:
            return False
        if extracted.get("signal") not in ALLOWED_SIGNALS:
            return False
        try:
            return score_product(
                ProductCardCreate(
                    product_name=extracted["product_name"],
                    category=extracted.get("category", "General"),
                    cost_of_goods=extracted["cost_of_goods"],
                    target_price=extracted["target_price"],
                    shipping_cost=extracted["shipping_cost"],
                    problem_or_desire_score=extracted["problem_or_desire_score"],
                    visual_potential_score=extracted["visual_potential_score"],
                    margin_score=extracted["margin_score"],
                    ad_risk_score=extracted["ad_risk_score"],
                    logistics_risk_score=extracted["logistics_risk_score"],
                )
            ).total_score is not None
        except Exception:
            return False


class SupplierCheckAgentService:
    def __init__(
        self,
        db: Session,
        mode: str | None = None,
        search_provider: SearchProvider | None = None,
        web_fetcher: WebPageFetcher | None = None,
        extractor: LLMExtractor | None = None,
    ):
        self.db = db
        self.mode = mode or settings.agent_mode
        self.search_provider = search_provider or get_search_provider(self.mode)
        self.web_fetcher = web_fetcher or get_fetch_provider(self.mode)
        self.extractor = extractor or get_llm_extractor(self.mode)

    def run(self, payload: SupplierCheckRunRequest) -> SupplierCheckRunResponse:
        trace_id = str(uuid.uuid4())
        prompt = load_prompt("supplier_check")
        snapshot = provider_snapshot(self.mode)

        run = create_agent_run(
            self.db,
            AgentType.supplier_check,
            payload.model_dump(),
            provider_snapshot=snapshot,
            trace_id=trace_id,
            hypothesis_id=payload.cycle_id,
            prompt_path=prompt["path"],
            prompt_version=prompt["version"],
        )
        warnings: list[str] = []

        try:
            mark_run_running(run)
            results: list[SupplierResult] = []

            for item in payload.shortlist_items:
                search_query = f"{item.product_name} supplier wholesale"
                supplier_links = self.search_provider.search(search_query, limit=2)
                add_task(self.db, run.id, "supplier_search", "completed", {"query": search_query}, {"count": len(supplier_links)})

                raw_text = ""
                if supplier_links:
                    raw_text = self.web_fetcher.fetch(supplier_links[0]["url"])
                extracted = self.extractor.extract_supplier_candidate(raw_text, prompt=prompt["content"])

                if settings.enable_raw_artifact_capture:
                    add_artifact(
                        self.db,
                        run.id,
                        "raw_supplier_extraction",
                        {"product_name": item.product_name, "supplier_links": supplier_links, "extracted": extracted},
                        uri=supplier_links[0]["url"] if supplier_links else None,
                        provider_name=self.extractor.name,
                        prompt_path=prompt["path"],
                        trace_id=trace_id,
                    )

                if not self._is_valid_supplier_extraction(extracted):
                    warnings.append(f"Invalid supplier extraction for product={item.product_name}")
                    continue

                economics = calculate_unit_economics(
                    UnitEconomicsInput(
                        cogs=extracted["unit_cost"],
                        shipping_cost=extracted["ship_cost"],
                        ad_cost_per_order=12,
                        transaction_fee=1.8,
                        selling_price=item.target_price,
                    )
                )

                if economics.margin_percent >= 35:
                    supplier_status = "passed"
                elif economics.margin_percent >= 20:
                    supplier_status = "quick_check"
                else:
                    supplier_status = "failed"

                result = SupplierResult(
                    product_name=item.product_name,
                    supplier_status=supplier_status,
                    contribution_margin=economics.contribution_margin,
                    recommendation=supplier_status,
                )
                results.append(result)
                add_decision_log(
                    self.db,
                    run.id,
                    item.product_name,
                    supplier_status,
                    f"Supplier={extracted['supplier_name']} margin={economics.margin_percent}",
                    score=economics.margin_percent,
                )

            if not results:
                raise AgentExecutionError("Supplier check produced no valid items after quality gates")

            final_recommendation = "passed" if any(r.supplier_status == "passed" for r in results) else "quick_check"
            if all(r.supplier_status == "failed" for r in results):
                final_recommendation = "failed"

            output = {
                "trace_id": trace_id,
                "results": [r.model_dump() for r in results],
                "final_recommendation": final_recommendation,
                "warnings": warnings,
            }
            add_artifact(
                self.db,
                run.id,
                "supplier_check_output",
                output,
                provider_name=self.search_provider.name,
                prompt_path=prompt["path"],
                trace_id=trace_id,
            )
            mark_run_completed(run, output, warnings=warnings)
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
            mark_run_failed(run, str(exc), warnings=warnings)
            self.db.commit()
            raise

    @staticmethod
    def _is_valid_supplier_extraction(extracted: dict) -> bool:
        required = ["supplier_name", "signal", "unit_cost", "ship_cost"]
        if any(field not in extracted for field in required):
            return False
        if not extracted["supplier_name"]:
            return False
        if extracted.get("signal") not in ALLOWED_SIGNALS:
            return False
        if extracted["unit_cost"] <= 0 or extracted["ship_cost"] < 0:
            return False
        return True


def get_agent_run(db: Session, run_id: int) -> AgentRun | None:
    return db.get(AgentRun, run_id)


def parse_run_payload(run: AgentRun) -> dict:
    return {
        "run_id": run.id,
        "agent_type": run.agent_type.value,
        "status": run.status.value,
        "trace_id": run.trace_id,
        "provider_snapshot": json.loads(run.provider_snapshot),
        "prompt_path": run.prompt_path,
        "prompt_version": run.prompt_version,
        "warnings": json.loads(run.warnings) if run.warnings else [],
        "input_payload": json.loads(run.input_payload),
        "output_payload": json.loads(run.output_payload) if run.output_payload else None,
        "error_message": run.error_message,
    }
