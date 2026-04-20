from app.schemas.hypothesis import ProductCardCreate
from app.services.scoring import score_product


def test_scoring_shortlist_threshold() -> None:
    payload = ProductCardCreate(
        product_name="A",
        category="B",
        cost_of_goods=10,
        target_price=30,
        shipping_cost=5,
        problem_or_desire_score=9,
        visual_potential_score=8,
        margin_score=8,
        ad_risk_score=7,
        logistics_risk_score=7,
    )
    result = score_product(payload)
    assert result.total_score >= 75
    assert result.decision == "shortlist"


def test_scoring_reject_threshold() -> None:
    payload = ProductCardCreate(
        product_name="A",
        category="B",
        cost_of_goods=10,
        target_price=20,
        shipping_cost=6,
        problem_or_desire_score=3,
        visual_potential_score=3,
        margin_score=4,
        ad_risk_score=4,
        logistics_risk_score=4,
    )
    result = score_product(payload)
    assert result.total_score < 55
    assert result.decision == "reject"
