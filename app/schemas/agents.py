from pydantic import BaseModel, Field


class ProductScoutRunRequest(BaseModel):
    market: str
    categories: list[str] = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    cycle_id: int | None = None


class ScoutCandidate(BaseModel):
    product_name: str
    category: str
    total_score: float
    decision: str


class ProductScoutRunResponse(BaseModel):
    run_id: int
    agent_type: str
    status: str
    shortlist: list[ScoutCandidate]
    reserve: list[ScoutCandidate]
    reject: list[ScoutCandidate]


class SupplierCheckItemInput(BaseModel):
    product_name: str
    target_price: float = Field(gt=0)
    cost_of_goods: float = Field(gt=0)
    shipping_cost: float = Field(ge=0)


class SupplierCheckRunRequest(BaseModel):
    shortlist_items: list[SupplierCheckItemInput] = Field(min_length=1)
    cycle_id: int | None = None


class SupplierResult(BaseModel):
    product_name: str
    supplier_status: str
    contribution_margin: float
    recommendation: str


class SupplierCheckRunResponse(BaseModel):
    run_id: int
    agent_type: str
    status: str
    results: list[SupplierResult]
    final_recommendation: str


class AgentRunStatusResponse(BaseModel):
    run_id: int
    agent_type: str
    status: str
    input_payload: dict
    output_payload: dict | None
    error_message: str | None
