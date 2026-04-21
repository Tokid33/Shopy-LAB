from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import DecisionCard, Incident, ProductHypothesis
from app.models.enums import HypothesisStatus, ResearchDecisionVerdict
from app.services.research import ResearchDecisionService, ResearchIngestionService, ResearchOrchestrator


def _seed_minimal_pack_with_normalization(db: Session, run_id: int) -> None:
    ingestion = ResearchIngestionService(db)
    ingestion.save_evidence(
        run_id=run_id,
        evidence_type="market",
        source_name="meta",
        content_excerpt="Strong market demand signals from ads.",
    )
    ingestion.save_evidence(
        run_id=run_id,
        evidence_type="voc",
        source_name="reddit",
        content_excerpt="Users have painful problem and will pay for convenience.",
    )
    ingestion.save_evidence(
        run_id=run_id,
        evidence_type="supplier",
        source_name="supplier_catalog",
        content_excerpt=(
            "Stable supplier with predictable lead time, low defect rate, clear SLA, "
            "verified packaging quality, and scalable capacity across seasonal peaks."
        ),
    )
    ingestion.save_evidence(
        run_id=run_id,
        evidence_type="economics",
        source_name="calc",
        content_excerpt=(
            "Healthy margin and contribution after shipping, payment fees and return reserve, "
            "with positive unit economics under conservative CAC assumptions."
        ),
    )
    ingestion.normalize_run_evidence(run_id)


def test_research_decision_pass_updates_hypothesis_status() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H-pass",
            problem_statement="Pain",
            target_audience="Audience",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.commit()

        run = ResearchOrchestrator(db).start_run(hypothesis.id)
        _seed_minimal_pack_with_normalization(db, run.id)

        summary = ResearchDecisionService(db).evaluate_run(run.id)

        assert summary.verdict in {ResearchDecisionVerdict.pass_, ResearchDecisionVerdict.hold}
        db.refresh(hypothesis)
        assert hypothesis.status in {HypothesisStatus.go, HypothesisStatus.scored}

        cards_count = db.scalar(select(func.count()).select_from(DecisionCard).where(DecisionCard.run_id == run.id))
        assert cards_count == 1


def test_research_decision_missing_signals_creates_hold_and_incident() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H-hold",
            problem_statement="Pain",
            target_audience="Audience",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.commit()

        run = ResearchOrchestrator(db).start_run(hypothesis.id)

        ingestion = ResearchIngestionService(db)
        ingestion.save_evidence(
            run_id=run.id,
            evidence_type="voc",
            source_name="forum",
            content_excerpt="Only one source is not enough for full decision.",
        )
        ingestion.normalize_run_evidence(run.id)

        summary = ResearchDecisionService(db).evaluate_run(run.id)

        assert summary.verdict == ResearchDecisionVerdict.hold
        db.refresh(hypothesis)
        assert hypothesis.status == HypothesisStatus.scored

        incident_count = db.scalar(select(func.count()).select_from(Incident).where(Incident.run_id == run.id))
        assert incident_count == 1
