from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import ProductCard, ProductHypothesis
from app.models.enums import HypothesisStatus


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
