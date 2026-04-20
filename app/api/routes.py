from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.workflow import run_demo_cycle

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/demo-cycle")
def demo_cycle(db: Session = Depends(get_db)) -> dict[str, str | int]:
    hypothesis = run_demo_cycle(db)
    return {"hypothesis_id": hypothesis.id, "status": hypothesis.status.value}
