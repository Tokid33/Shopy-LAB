from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AgentRunStatus, ResearchDecisionVerdict


class ResearchRunCreateResponse(BaseModel):
    run_id: int
    hypothesis_id: int
    status: AgentRunStatus
    planned_tasks: list[str]


class ResearchRunStatusResponse(BaseModel):
    run_id: int
    hypothesis_id: int | None
    status: AgentRunStatus
    tasks: list[dict]


class DecisionCardResponse(BaseModel):
    id: int
    hypothesis_id: int
    run_id: int | None
    verdict: ResearchDecisionVerdict
    confidence: float
    rationale: str
    created_at: datetime
