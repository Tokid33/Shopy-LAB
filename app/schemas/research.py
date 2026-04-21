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


class EvidenceIngestRequest(BaseModel):
    evidence_type: str
    source_name: str
    content_excerpt: str
    source_uri: str | None = None


class EvidenceIngestResponse(BaseModel):
    evidence_id: int
    minimal_signal_pack_ready: bool


class NormalizationResponse(BaseModel):
    run_id: int
    created_signals: int
    minimal_signal_pack_ready: bool


class EvaluationResponse(BaseModel):
    hypothesis_id: int
    run_id: int
    verdict: ResearchDecisionVerdict
    score_value: float
    confidence: float
    rationale: str
    red_flags: list[str]
