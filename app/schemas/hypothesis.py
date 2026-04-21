from pydantic import BaseModel, Field


class ProductHypothesisCreate(BaseModel):
    title: str
    problem_statement: str
    target_audience: str


class ProductCardCreate(BaseModel):
    product_name: str
    category: str
    cost_of_goods: float = Field(gt=0)
    target_price: float = Field(gt=0)
    shipping_cost: float = Field(ge=0)
    problem_or_desire_score: int = Field(ge=1, le=10)
    visual_potential_score: int = Field(ge=1, le=10)
    margin_score: int = Field(ge=1, le=10)
    ad_risk_score: int = Field(ge=1, le=10)
    logistics_risk_score: int = Field(ge=1, le=10)


class ScoreResult(BaseModel):
    total_score: float
    decision: str
    explanation: str
