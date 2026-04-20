from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FinalDecision, Postmortem
from app.schemas.decision import FinalDecisionCreate, PostmortemCreate


class FinalizationError(ValueError):
    pass


def register_final_decision(
    db: Session,
    hypothesis_id: int,
    decision_payload: FinalDecisionCreate,
    postmortem_payload: PostmortemCreate,
) -> tuple[FinalDecision, Postmortem]:
    existing = db.scalar(select(FinalDecision).where(FinalDecision.hypothesis_id == hypothesis_id))
    if existing:
        raise FinalizationError("Final decision already exists for this hypothesis")

    if decision_payload.final_outcome != postmortem_payload.next_action:
        raise FinalizationError("Final decision and postmortem next_action must match")

    final_decision = FinalDecision(hypothesis_id=hypothesis_id, **decision_payload.model_dump())
    postmortem = Postmortem(hypothesis_id=hypothesis_id, **postmortem_payload.model_dump())

    db.add(final_decision)
    db.add(postmortem)
    db.flush()

    return final_decision, postmortem
