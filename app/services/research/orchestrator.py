from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, AgentTask, DecisionCard, ProductHypothesis
from app.models.enums import AgentRunStatus, AgentType


class ResearchOrchestrator:
    """Step 3/4 skeleton orchestrator for research runs."""

    PLANNED_TASKS = ["scout", "voc", "supplier", "decision"]

    def __init__(self, db: Session):
        self.db = db

    def start_run(self, hypothesis_id: int) -> AgentRun:
        hypothesis = self.db.get(ProductHypothesis, hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        run = AgentRun(
            hypothesis_id=hypothesis_id,
            agent_type=AgentType.product_scout,
            status=AgentRunStatus.created,
            trace_id=f"research-{hypothesis_id}-{int(datetime.utcnow().timestamp())}",
            provider_snapshot=json.dumps({"mode": "research_orchestrator", "version": "v1.1"}),
            prompt_path=None,
            prompt_version=None,
            input_payload=json.dumps({"hypothesis_id": hypothesis_id, "flow": "research_v1_1"}),
        )
        self.db.add(run)
        self.db.flush()

        for task_name in self.PLANNED_TASKS:
            task = AgentTask(
                run_id=run.id,
                task_name=task_name,
                status="planned",
                input_payload=json.dumps({"hypothesis_id": hypothesis_id}),
            )
            self.db.add(task)

        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: int) -> AgentRun | None:
        return self.db.get(AgentRun, run_id)

    def get_decision_card(self, hypothesis_id: int) -> DecisionCard | None:
        stmt = (
            select(DecisionCard)
            .where(DecisionCard.hypothesis_id == hypothesis_id)
            .order_by(DecisionCard.created_at.desc(), DecisionCard.id.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
