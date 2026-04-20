from app.services.unit_economics import UnitEconomicsInput, calculate_unit_economics


def test_unit_economics_calculation() -> None:
    payload = UnitEconomicsInput(
        cogs=12,
        shipping_cost=4,
        ad_cost_per_order=10,
        transaction_fee=2,
        selling_price=39,
    )
    result = calculate_unit_economics(payload)

    assert result.contribution_margin == 11
    assert result.margin_percent == round((11 / 39) * 100, 2)
    assert result.break_even_roas == 3.9
