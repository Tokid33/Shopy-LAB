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
