from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Decision, ProductHypothesis
from app.models.enums import HypothesisLifecycleState, LandingPageState, TrafficTestState
from app.services.workflow import run_demo_cycle


def test_demo_cycle_smoke() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = run_demo_cycle(db)

        loaded = db.scalar(select(ProductHypothesis).where(ProductHypothesis.id == hypothesis.id))
        assert loaded is not None
        assert loaded.product_card is not None
        assert len(loaded.competitor_snapshots) >= 5
        assert len(loaded.supplier_assessments) >= 1
        assert loaded.unit_economics is not None
        assert loaded.final_decision is not None
        assert loaded.postmortem is not None
        assert loaded.lifecycle_state == HypothesisLifecycleState.finalized
        assert loaded.offers[0].landing_pages[0].lifecycle_state == LandingPageState.ready_for_traffic
        assert loaded.traffic_tests[0].lifecycle_state == TrafficTestState.completed

        decisions = db.scalars(select(Decision).where(Decision.hypothesis_id == loaded.id)).all()
        assert len(decisions) >= 1
