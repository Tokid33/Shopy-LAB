from enum import Enum


class HypothesisStatus(str, Enum):
    draft = "draft"
    scored = "scored"
    go = "go"
    no_go = "no_go"


class ProductDecision(str, Enum):
    shortlist = "shortlist"
    reserve = "reserve"
    reject = "reject"


class SiteDecision(str, Enum):
    ready_for_traffic = "ready_for_traffic"
    not_ready = "not_ready"


class TrafficDecision(str, Enum):
    kill = "kill"
    iterate = "iterate"
    scale = "scale"


class DecisionStage(str, Enum):
    product = "product"
    site = "site"
    traffic = "traffic"
    final = "final"


class AgentRunStatus(str, Enum):
    created = "created"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentType(str, Enum):
    product_scout = "product_scout"
    supplier_check = "supplier_check"


class HypothesisLifecycleState(str, Enum):
    product_discovery = "product_discovery"
    site_ready = "site_ready"
    traffic_running = "traffic_running"
    traffic_completed = "traffic_completed"
    finalized = "finalized"


class LandingPageState(str, Enum):
    draft = "draft"
    ready_for_traffic = "ready_for_traffic"


class TrafficTestState(str, Enum):
    planned = "planned"
    running = "running"
    completed = "completed"


class FinalDecisionState(str, Enum):
    recorded = "recorded"


class ResearchSignalType(str, Enum):
    problem_severity = "problem_severity"
    willingness_to_pay = "willingness_to_pay"
    market_competition = "market_competition"
    supplier_reliability = "supplier_reliability"
    unit_economics = "unit_economics"
    policy_risk = "policy_risk"


class ResearchDecisionVerdict(str, Enum):
    pass_ = "pass"
    hold = "hold"
    reject = "reject"


class IncidentSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
