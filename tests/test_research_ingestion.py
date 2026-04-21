from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import NormalizedSignal, ProductHypothesis
from app.models.enums import HypothesisStatus
from app.services.research import ResearchIngestionService, ResearchOrchestrator


def test_ingestion_and_normalization_flow() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H2",
            problem_statement="Pain",
            target_audience="Audience",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.commit()

        orchestrator = ResearchOrchestrator(db)
        run = orchestrator.start_run(hypothesis.id)

        ingestion = ResearchIngestionService(db)
        summary_market = ingestion.save_evidence(
            run_id=run.id,
            evidence_type="market",
            source_name="meta_ad_library",
            content_excerpt="Winning ads repeat clear value proposition and bundles.",
        )
        assert summary_market.minimal_signal_pack_ready is False

        ingestion.save_evidence(
            run_id=run.id,
            evidence_type="voc",
            source_name="reddit",
            content_excerpt="Users complain about setup complexity and returns.",
        )
        summary_supplier = ingestion.save_evidence(
            run_id=run.id,
            evidence_type="supplier",
            source_name="1688",
            content_excerpt="MOQ 300, stable lead-time, medium shipping risk.",
        )
        assert summary_supplier.minimal_signal_pack_ready is True

        normalized = ingestion.normalize_run_evidence(run.id)
        assert normalized.created_signals == 3
        assert normalized.minimal_signal_pack_ready is True

        signal_count = db.scalar(
            select(func.count()).select_from(NormalizedSignal).where(NormalizedSignal.hypothesis_id == hypothesis.id)
        )
        assert signal_count == 3
