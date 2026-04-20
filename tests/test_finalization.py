import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import ProductHypothesis
from app.models.enums import HypothesisStatus
from app.schemas.decision import FinalDecisionCreate, PostmortemCreate
from app.services.finalization import FinalizationError, register_final_decision


def test_finalization_rejects_duplicate_decision() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H1",
            problem_statement="P",
            target_audience="A",
            status=HypothesisStatus.go,
        )
        db.add(hypothesis)
        db.commit()

        decision = FinalDecisionCreate(
            final_outcome="iterate",
            confidence=7,
            rationale="Достаточно данных для итерации.",
            owner="ops",
        )
        postmortem = PostmortemCreate(
            what_worked="Угол time-saving дал качественный отклик аудитории.",
            what_failed="Статичные креативы отработали хуже видео форматов.",
            key_risks="Есть риск роста CPA при масштабировании в текущем виде.",
            next_action="iterate",
            lessons="Сначала продавать рутину, потом спецификацию продукта.",
        )

        register_final_decision(db, hypothesis.id, decision, postmortem)
        db.commit()

        with pytest.raises(FinalizationError):
            register_final_decision(db, hypothesis.id, decision, postmortem)


def test_finalization_requires_consistent_outcome() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H2",
            problem_statement="P",
            target_audience="A",
            status=HypothesisStatus.go,
        )
        db.add(hypothesis)
        db.commit()

        decision = FinalDecisionCreate(
            final_outcome="scale",
            confidence=8,
            rationale="ROAS стабильно выше порога.",
            owner="ops",
        )
        inconsistent_postmortem = PostmortemCreate(
            what_worked="Видео креативы дали сильный CTR и конверсию.",
            what_failed="Часть аудиторий быстро выжглась по частоте показов.",
            key_risks="Риск деградации эффективности при резком росте бюджета.",
            next_action="iterate",
            lessons="Нужен контролируемый рост бюджета волнами.",
        )

        with pytest.raises(FinalizationError):
            register_final_decision(db, hypothesis.id, decision, inconsistent_postmortem)
