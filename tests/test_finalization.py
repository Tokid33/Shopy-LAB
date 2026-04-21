import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import ProductHypothesis, TrafficTest
from app.models.enums import HypothesisLifecycleState, HypothesisStatus, TrafficTestState
from app.schemas.decision import FinalDecisionCreate, PostmortemCreate
from app.services.finalization import FinalizationError, register_final_decision


def _create_ready_for_finalization_hypothesis(db: Session, title: str) -> ProductHypothesis:
    hypothesis = ProductHypothesis(
        title=title,
        problem_statement="P",
        target_audience="A",
        status=HypothesisStatus.go,
        lifecycle_state=HypothesisLifecycleState.traffic_completed,
    )
    db.add(hypothesis)
    db.flush()

    traffic = TrafficTest(
        hypothesis_id=hypothesis.id,
        channel="Meta",
        budget=100,
        test_plan="demo",
        lifecycle_state=TrafficTestState.completed,
    )
    db.add(traffic)
    db.commit()
    return hypothesis


def test_finalization_rejects_duplicate_decision() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = _create_ready_for_finalization_hypothesis(db, "H1")

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
        hypothesis = _create_ready_for_finalization_hypothesis(db, "H2")

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


def test_finalization_requires_completed_traffic_state() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="H3",
            problem_statement="P",
            target_audience="A",
            status=HypothesisStatus.go,
            lifecycle_state=HypothesisLifecycleState.site_ready,
        )
        db.add(hypothesis)
        db.commit()

        decision = FinalDecisionCreate(
            final_outcome="kill",
            confidence=6,
            rationale="Недостаточно сигнала.",
            owner="ops",
        )
        postmortem = PostmortemCreate(
            what_worked="Часть сегментов дала дешевые клики.",
            what_failed="Конверсии в покупку не вышли на целевой уровень.",
            key_risks="Рост CPA при попытке масштабирования.",
            next_action="kill",
            lessons="Не запускать масштаб без валидации оффера.",
        )

        with pytest.raises(FinalizationError):
            register_final_decision(db, hypothesis.id, decision, postmortem)
