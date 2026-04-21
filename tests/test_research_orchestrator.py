from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import ProductHypothesis
from app.models.enums import HypothesisStatus
from app.services.research import ResearchOrchestrator


def test_start_research_run_creates_planned_tasks() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H1",
            problem_statement="Pain",
            target_audience="Audience",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.commit()

        orchestrator = ResearchOrchestrator(db)
        run = orchestrator.start_run(hypothesis.id)

        assert run.hypothesis_id == hypothesis.id
        assert run.status.value == "created"
        assert sorted([task.task_name for task in run.tasks]) == sorted(ResearchOrchestrator.PLANNED_TASKS)
        assert all(task.status == "planned" for task in run.tasks)
