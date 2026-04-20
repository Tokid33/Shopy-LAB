from pydantic import BaseModel, Field


class UnitEconomicsInput(BaseModel):
    cogs: float = Field(gt=0)
    shipping_cost: float = Field(ge=0)
    ad_cost_per_order: float = Field(ge=0)
    transaction_fee: float = Field(ge=0)
    selling_price: float = Field(gt=0)


class UnitEconomicsResult(BaseModel):
    contribution_margin: float
    margin_percent: float
    break_even_roas: float


def calculate_unit_economics(payload: UnitEconomicsInput) -> UnitEconomicsResult:
    total_variable_cost = (
        payload.cogs
        + payload.shipping_cost
        + payload.ad_cost_per_order
        + payload.transaction_fee
    )
    contribution_margin = round(payload.selling_price - total_variable_cost, 2)
    margin_percent = round((contribution_margin / payload.selling_price) * 100, 2)
    break_even_roas = round(payload.selling_price / max(payload.ad_cost_per_order, 0.01), 2)

    return UnitEconomicsResult(
        contribution_margin=contribution_margin,
        margin_percent=margin_percent,
        break_even_roas=break_even_roas,
    )
