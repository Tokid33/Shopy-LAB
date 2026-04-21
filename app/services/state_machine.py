from app.models import FinalDecision, LandingPage, ProductHypothesis, TrafficTest
from app.models.enums import (
    FinalDecisionState,
    HypothesisLifecycleState,
    LandingPageState,
    TrafficTestState,
)


class InvalidStateTransitionError(ValueError):
    pass


def mark_landing_ready(hypothesis: ProductHypothesis, landing_page: LandingPage) -> None:
    if not landing_page.mobile_ready:
        raise InvalidStateTransitionError("Landing page must be mobile_ready before ready_for_traffic")
    landing_page.lifecycle_state = LandingPageState.ready_for_traffic
    hypothesis.lifecycle_state = HypothesisLifecycleState.site_ready


def start_traffic_test(hypothesis: ProductHypothesis, landing_page: LandingPage, traffic_test: TrafficTest) -> None:
    if hypothesis.lifecycle_state != HypothesisLifecycleState.site_ready:
        raise InvalidStateTransitionError("Hypothesis must be site_ready before traffic start")
    if landing_page.lifecycle_state != LandingPageState.ready_for_traffic:
        raise InvalidStateTransitionError("Landing page must be ready_for_traffic before traffic start")
    traffic_test.lifecycle_state = TrafficTestState.running
    hypothesis.lifecycle_state = HypothesisLifecycleState.traffic_running


def complete_traffic_test(hypothesis: ProductHypothesis, traffic_test: TrafficTest) -> None:
    if traffic_test.lifecycle_state != TrafficTestState.running:
        raise InvalidStateTransitionError("Traffic test must be running before completion")
    traffic_test.lifecycle_state = TrafficTestState.completed
    hypothesis.lifecycle_state = HypothesisLifecycleState.traffic_completed


def finalize_hypothesis_state(
    hypothesis: ProductHypothesis,
    traffic_test: TrafficTest,
    final_decision: FinalDecision | None,
    next_action: str,
) -> None:
    if final_decision is not None:
        raise InvalidStateTransitionError("Hypothesis already finalized")
    if hypothesis.lifecycle_state != HypothesisLifecycleState.traffic_completed:
        raise InvalidStateTransitionError("Hypothesis must have completed traffic before finalization")
    if traffic_test.lifecycle_state != TrafficTestState.completed:
        raise InvalidStateTransitionError("Traffic test must be completed before finalization")
    if next_action not in {"kill", "iterate", "scale"}:
        raise InvalidStateTransitionError("Invalid next_action for finalization")


def mark_finalized(hypothesis: ProductHypothesis, final_decision: FinalDecision) -> None:
    final_decision.lifecycle_state = FinalDecisionState.recorded
    hypothesis.lifecycle_state = HypothesisLifecycleState.finalized
