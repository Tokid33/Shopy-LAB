from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    AgentRun,
    DecisionCard,
    NormalizedSignal,
    ProductCard,
    ProductHypothesis,
    ProductScore,
    SourceEvidence,
)
from app.models.enums import (
    AgentRunStatus,
    AgentType,
    HypothesisStatus,
    ResearchDecisionVerdict,
    ResearchSignalType,
)


def test_hypothesis_and_product_card_link() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="Test",
            problem_statement="Problem",
            target_audience="Audience",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.flush()

        card = ProductCard(
            hypothesis_id=hypothesis.id,
            product_name="Demo",
            category="Cat",
            cost_of_goods=10,
            target_price=25,
            shipping_cost=3,
            problem_or_desire_score=7,
            visual_potential_score=7,
            margin_score=7,
            ad_risk_score=7,
            logistics_risk_score=7,
            total_score=70,
            product_decision="reserve",
        )
        db.add(card)
        db.commit()

        db.refresh(hypothesis)
        assert hypothesis.product_card is not None
        assert hypothesis.product_card.product_name == "Demo"


def test_research_entities_link_to_hypothesis() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="Research test",
            problem_statement="Pain",
            target_audience="Niche",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.flush()

        run = AgentRun(
            hypothesis_id=hypothesis.id,
            agent_type=AgentType.product_scout,
            status=AgentRunStatus.created,
            trace_id="trace-research-1",
            provider_snapshot='{"provider":"mock"}',
            prompt_path=None,
            prompt_version=None,
            input_payload="{}",
        )
        db.add(run)
        db.flush()

        evidence = SourceEvidence(
            hypothesis_id=hypothesis.id,
            run_id=run.id,
            evidence_type="voc_quote",
            source_name="reddit",
            source_uri="https://example.test/thread",
            content_excerpt="Customers say this solves a daily pain.",
        )
        db.add(evidence)
        db.flush()

        signal = NormalizedSignal(
            hypothesis_id=hypothesis.id,
            evidence_id=evidence.id,
            signal_type=ResearchSignalType.problem_severity,
            value=0.88,
            confidence=0.72,
            rationale="Repeated pain mention frequency is high.",
        )
        score = ProductScore(
            hypothesis_id=hypothesis.id,
            run_id=run.id,
            score_value=78.5,
            confidence=0.69,
            score_breakdown='{"problem":0.88}',
        )
        decision_card = DecisionCard(
            hypothesis_id=hypothesis.id,
            run_id=run.id,
            verdict=ResearchDecisionVerdict.hold,
            confidence=0.61,
            rationale="Need stronger supplier confirmation.",
        )
        db.add_all([signal, score, decision_card])
        db.commit()

        db.refresh(hypothesis)
        assert len(hypothesis.source_evidences) == 1
        assert len(hypothesis.normalized_signals) == 1
        assert len(hypothesis.product_scores) == 1
        assert len(hypothesis.decision_cards) == 1
