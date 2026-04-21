import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import LandingPage, Offer, ProductHypothesis, TrafficTest
from app.models.enums import HypothesisLifecycleState, HypothesisStatus, LandingPageState, TrafficTestState
from app.services.state_machine import (
    InvalidStateTransitionError,
    complete_traffic_test,
    mark_landing_ready,
    start_traffic_test,
)


def _seed_entities(db: Session):
    hypothesis = ProductHypothesis(
        title="H",
        problem_statement="P",
        target_audience="A",
        status=HypothesisStatus.scored,
        lifecycle_state=HypothesisLifecycleState.product_discovery,
    )
    db.add(hypothesis)
    db.flush()

    offer = Offer(hypothesis_id=hypothesis.id, title="T", angle="A", value_proposition="V")
    db.add(offer)
    db.flush()

    landing = LandingPage(
        offer_id=offer.id,
        hero_block="h",
        benefits_block="b",
        proof_block="p",
        offer_block="o",
        faq_block="f",
        mobile_ready=1,
        lifecycle_state=LandingPageState.draft,
    )
    traffic = TrafficTest(
        hypothesis_id=hypothesis.id,
        channel="Meta",
        budget=100,
        test_plan="t",
        lifecycle_state=TrafficTestState.planned,
    )
    db.add(landing)
    db.add(traffic)
    db.flush()
    return hypothesis, landing, traffic


def test_valid_state_transitions() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis, landing, traffic = _seed_entities(db)

        mark_landing_ready(hypothesis, landing)
        start_traffic_test(hypothesis, landing, traffic)
        complete_traffic_test(hypothesis, traffic)

        assert hypothesis.lifecycle_state == HypothesisLifecycleState.traffic_completed
        assert landing.lifecycle_state == LandingPageState.ready_for_traffic
        assert traffic.lifecycle_state == TrafficTestState.completed


def test_invalid_transition_traffic_before_site_ready() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis, landing, traffic = _seed_entities(db)
        with pytest.raises(InvalidStateTransitionError):
            start_traffic_test(hypothesis, landing, traffic)
