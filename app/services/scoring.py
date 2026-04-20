from app.schemas.hypothesis import ProductCardCreate, ScoreResult

WEIGHTS = {
    "problem_or_desire_score": 0.30,
    "visual_potential_score": 0.20,
    "margin_score": 0.25,
    "ad_risk_score": 0.15,
    "logistics_risk_score": 0.10,
}


def score_product(card: ProductCardCreate) -> ScoreResult:
    weighted = (
        card.problem_or_desire_score * WEIGHTS["problem_or_desire_score"]
        + card.visual_potential_score * WEIGHTS["visual_potential_score"]
        + card.margin_score * WEIGHTS["margin_score"]
        + card.ad_risk_score * WEIGHTS["ad_risk_score"]
        + card.logistics_risk_score * WEIGHTS["logistics_risk_score"]
    )

    total_score = round(weighted * 10, 2)

    if total_score >= 75:
        decision = "shortlist"
    elif total_score >= 55:
        decision = "reserve"
    else:
        decision = "reject"

    explanation = (
        "Rule-based score = сумма(оценка * вес) * 10. "
        f"Итог: {total_score}, решение: {decision}."
    )
    return ScoreResult(total_score=total_score, decision=decision, explanation=explanation)
