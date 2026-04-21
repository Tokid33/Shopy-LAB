from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FinalDecision, Postmortem, ProductHypothesis, TrafficTest
from app.schemas.decision import FinalDecisionCreate, PostmortemCreate
from app.services.state_machine import (
    InvalidStateTransitionError,
    finalize_hypothesis_state,
    mark_finalized,
)


class FinalizationError(ValueError):
    pass


def register_final_decision(
    db: Session,
    hypothesis_id: int,
    decision_payload: FinalDecisionCreate,
    postmortem_payload: PostmortemCreate,
) -> tuple[FinalDecision, Postmortem]:
    hypothesis = db.get(ProductHypothesis, hypothesis_id)
    if not hypothesis:
        raise FinalizationError(f"Hypothesis {hypothesis_id} not found")

    existing = db.scalar(select(FinalDecision).where(FinalDecision.hypothesis_id == hypothesis_id))
    if existing:
        raise FinalizationError("Final decision already exists for this hypothesis")

    if decision_payload.final_outcome != postmortem_payload.next_action:
        raise FinalizationError("Final decision and postmortem next_action must match")

    traffic_test = db.scalar(
        select(TrafficTest).where(TrafficTest.hypothesis_id == hypothesis_id).order_by(TrafficTest.id.desc())
    )
    if not traffic_test:
        raise FinalizationError("Final decision requires completed traffic test")

    try:
        finalize_hypothesis_state(
            hypothesis=hypothesis,
            traffic_test=traffic_test,
            final_decision=existing,
            next_action=postmortem_payload.next_action,
        )
    except InvalidStateTransitionError as exc:
        raise FinalizationError(str(exc)) from exc

    final_decision = FinalDecision(hypothesis_id=hypothesis_id, **decision_payload.model_dump())
    postmortem = Postmortem(hypothesis_id=hypothesis_id, **postmortem_payload.model_dump())

    db.add(final_decision)
    db.add(postmortem)
    db.flush()
    mark_finalized(hypothesis, final_decision)

    return final_decision, postmortem
