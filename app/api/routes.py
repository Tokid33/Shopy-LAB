from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.hypothesis_repository import ProductHypothesisRepository
from app.schemas.agents import (
    AgentRunStatusResponse,
    ProductScoutRunRequest,
    ProductScoutRunResponse,
    SupplierCheckRunRequest,
    SupplierCheckRunResponse,
)
from app.schemas.hypothesis import (
    ProductHypothesisCreate,
    ProductHypothesisResponse,
    ProductHypothesisUpdate,
)
from app.schemas.research import (
    DecisionCardResponse,
    EvidenceIngestRequest,
    EvidenceIngestResponse,
    EvaluationResponse,
    NormalizationResponse,
    ResearchRunCreateResponse,
    ResearchRunStatusResponse,
)
from app.services.agents.services import (
    AgentExecutionError,
    ProductScoutAgentService,
    SupplierCheckAgentService,
    get_agent_run,
    parse_run_payload,
)
from app.services.agents.providers import ProviderResolutionError, provider_health
from app.services.research import ResearchDecisionService, ResearchIngestionService, ResearchOrchestrator
from app.services.workflow import run_demo_cycle

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/demo-cycle")
def demo_cycle(db: Session = Depends(get_db)) -> dict[str, str | int]:
    hypothesis = run_demo_cycle(db)
    return {"hypothesis_id": hypothesis.id, "status": hypothesis.status.value}


@router.post("/agents/product-scout/run", response_model=ProductScoutRunResponse)
def run_product_scout_agent(payload: ProductScoutRunRequest, db: Session = Depends(get_db)) -> ProductScoutRunResponse:
    service = ProductScoutAgentService(db)
    return service.run(payload)


@router.post("/agents/supplier-check/run", response_model=SupplierCheckRunResponse)
def run_supplier_check_agent(payload: SupplierCheckRunRequest, db: Session = Depends(get_db)) -> SupplierCheckRunResponse:
    service = SupplierCheckAgentService(db)
    return service.run(payload)


@router.post("/agents/product-scout/run-real", response_model=ProductScoutRunResponse)
def run_product_scout_agent_real(payload: ProductScoutRunRequest, db: Session = Depends(get_db)) -> ProductScoutRunResponse:
    try:
        service = ProductScoutAgentService(db, mode="real")
        return service.run(payload)
    except (ProviderResolutionError, AgentExecutionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/agents/supplier-check/run-real", response_model=SupplierCheckRunResponse)
def run_supplier_check_agent_real(payload: SupplierCheckRunRequest, db: Session = Depends(get_db)) -> SupplierCheckRunResponse:
    try:
        service = SupplierCheckAgentService(db, mode="real")
        return service.run(payload)
    except (ProviderResolutionError, AgentExecutionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/agents/providers/health")
def get_providers_health() -> dict:
    return provider_health()


@router.get("/agents/runs/{run_id}", response_model=AgentRunStatusResponse)
def get_agent_run_status(run_id: int, db: Session = Depends(get_db)) -> AgentRunStatusResponse:
    run = get_agent_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Agent run {run_id} not found")
    return AgentRunStatusResponse(**parse_run_payload(run))


@router.post("/hypotheses", response_model=ProductHypothesisResponse)
def create_hypothesis(payload: ProductHypothesisCreate, db: Session = Depends(get_db)) -> ProductHypothesisResponse:
    repo = ProductHypothesisRepository(db)
    entity = repo.create(payload)
    db.commit()
    db.refresh(entity)
    return ProductHypothesisResponse.model_validate(entity, from_attributes=True)


@router.get("/hypotheses/{hypothesis_id}", response_model=ProductHypothesisResponse)
def get_hypothesis(hypothesis_id: int, db: Session = Depends(get_db)) -> ProductHypothesisResponse:
    repo = ProductHypothesisRepository(db)
    entity = repo.get(hypothesis_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Hypothesis {hypothesis_id} not found")
    return ProductHypothesisResponse.model_validate(entity, from_attributes=True)


@router.patch("/hypotheses/{hypothesis_id}", response_model=ProductHypothesisResponse)
def patch_hypothesis(
    hypothesis_id: int, payload: ProductHypothesisUpdate, db: Session = Depends(get_db)
) -> ProductHypothesisResponse:
    repo = ProductHypothesisRepository(db)
    entity = repo.get(hypothesis_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Hypothesis {hypothesis_id} not found")
    updated = repo.update(entity, payload)
    return ProductHypothesisResponse.model_validate(updated, from_attributes=True)


@router.post("/hypotheses/{hypothesis_id}/research-runs", response_model=ResearchRunCreateResponse)
def create_research_run(hypothesis_id: int, db: Session = Depends(get_db)) -> ResearchRunCreateResponse:
    orchestrator = ResearchOrchestrator(db)
    try:
        run = orchestrator.start_run(hypothesis_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResearchRunCreateResponse(
        run_id=run.id,
        hypothesis_id=hypothesis_id,
        status=run.status,
        planned_tasks=ResearchOrchestrator.PLANNED_TASKS,
    )


@router.get("/research-runs/{run_id}", response_model=ResearchRunStatusResponse)
def get_research_run(run_id: int, db: Session = Depends(get_db)) -> ResearchRunStatusResponse:
    orchestrator = ResearchOrchestrator(db)
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Research run {run_id} not found")
    return ResearchRunStatusResponse(
        run_id=run.id,
        hypothesis_id=run.hypothesis_id,
        status=run.status,
        tasks=[{"id": task.id, "name": task.task_name, "status": task.status} for task in run.tasks],
    )


@router.get("/hypotheses/{hypothesis_id}/decision-card", response_model=DecisionCardResponse)
def get_hypothesis_decision_card(hypothesis_id: int, db: Session = Depends(get_db)) -> DecisionCardResponse:
    orchestrator = ResearchOrchestrator(db)
    card = orchestrator.get_decision_card(hypothesis_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Decision card for hypothesis {hypothesis_id} not found")
    return DecisionCardResponse.model_validate(card, from_attributes=True)


@router.post("/research-runs/{run_id}/evidence", response_model=EvidenceIngestResponse)
def ingest_research_evidence(
    run_id: int, payload: EvidenceIngestRequest, db: Session = Depends(get_db)
) -> EvidenceIngestResponse:
    ingestion = ResearchIngestionService(db)
    try:
        summary = ingestion.save_evidence(
            run_id=run_id,
            evidence_type=payload.evidence_type,
            source_name=payload.source_name,
            content_excerpt=payload.content_excerpt,
            source_uri=payload.source_uri,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvidenceIngestResponse(
        evidence_id=summary.created_evidence_id,
        minimal_signal_pack_ready=summary.minimal_signal_pack_ready,
    )


@router.post("/research-runs/{run_id}/normalize", response_model=NormalizationResponse)
def normalize_research_run(run_id: int, db: Session = Depends(get_db)) -> NormalizationResponse:
    ingestion = ResearchIngestionService(db)
    try:
        summary = ingestion.normalize_run_evidence(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return NormalizationResponse(
        run_id=summary.run_id,
        created_signals=summary.created_signals,
        minimal_signal_pack_ready=summary.minimal_signal_pack_ready,
    )


@router.post("/research-runs/{run_id}/evaluate", response_model=EvaluationResponse)
def evaluate_research_run(run_id: int, db: Session = Depends(get_db)) -> EvaluationResponse:
    service = ResearchDecisionService(db)
    try:
        summary = service.evaluate_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvaluationResponse(
        hypothesis_id=summary.hypothesis_id,
        run_id=summary.run_id,
        verdict=summary.verdict,
        score_value=summary.score_value,
        confidence=summary.confidence,
        rationale=summary.rationale,
        red_flags=summary.red_flags,
    )
