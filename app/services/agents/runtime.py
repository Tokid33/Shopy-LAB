import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AgentArtifact, AgentDecisionLog, AgentRun, AgentTask
from app.models.enums import AgentRunStatus, AgentType


def create_agent_run(db: Session, agent_type: AgentType, input_payload: dict, hypothesis_id: int | None = None) -> AgentRun:
    run = AgentRun(
        hypothesis_id=hypothesis_id,
        agent_type=agent_type,
        status=AgentRunStatus.created,
        input_payload=json.dumps(input_payload, ensure_ascii=False),
    )
    db.add(run)
    db.flush()
    return run


def mark_run_running(run: AgentRun) -> None:
    run.status = AgentRunStatus.running


def mark_run_completed(run: AgentRun, output_payload: dict) -> None:
    run.status = AgentRunStatus.completed
    run.output_payload = json.dumps(output_payload, ensure_ascii=False)
    run.finished_at = datetime.utcnow()


def mark_run_failed(run: AgentRun, message: str) -> None:
    run.status = AgentRunStatus.failed
    run.error_message = message
    run.finished_at = datetime.utcnow()


def add_task(db: Session, run_id: int, task_name: str, status: str, input_payload: dict, output_payload: dict | None = None, error_message: str | None = None) -> None:
    db.add(
        AgentTask(
            run_id=run_id,
            task_name=task_name,
            status=status,
            input_payload=json.dumps(input_payload, ensure_ascii=False),
            output_payload=json.dumps(output_payload, ensure_ascii=False) if output_payload is not None else None,
            error_message=error_message,
        )
    )


def add_artifact(db: Session, run_id: int, artifact_type: str, payload: dict, uri: str | None = None) -> None:
    db.add(
        AgentArtifact(
            run_id=run_id,
            artifact_type=artifact_type,
            content_uri=uri,
            content_payload=json.dumps(payload, ensure_ascii=False),
        )
    )


def add_decision_log(db: Session, run_id: int, item_ref: str, decision: str, rationale: str, score: float | None = None) -> None:
    db.add(
        AgentDecisionLog(
            run_id=run_id,
            item_ref=item_ref,
            decision=decision,
            rationale=rationale,
            score=score,
        )
    )
