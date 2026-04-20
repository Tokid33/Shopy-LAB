from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agents import (
    AgentRunStatusResponse,
    ProductScoutRunRequest,
    ProductScoutRunResponse,
    SupplierCheckRunRequest,
    SupplierCheckRunResponse,
)
from app.services.agents.services import (
    ProductScoutAgentService,
    SupplierCheckAgentService,
    get_agent_run,
    parse_run_payload,
)
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


@router.get("/agents/runs/{run_id}", response_model=AgentRunStatusResponse)
def get_agent_run_status(run_id: int, db: Session = Depends(get_db)) -> AgentRunStatusResponse:
    run = get_agent_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Agent run {run_id} not found")
    return AgentRunStatusResponse(**parse_run_payload(run))
