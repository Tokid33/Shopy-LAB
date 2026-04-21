"""add research stage foundation tables

Revision ID: 0006_research_stage_foundation
Revises: 0005_state_machine_fields
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_research_stage_foundation"
down_revision = "0005_state_machine_fields"
branch_labels = None
depends_on = None


research_signal_enum = sa.Enum(
    "problem_severity",
    "willingness_to_pay",
    "market_competition",
    "supplier_reliability",
    "unit_economics",
    "policy_risk",
    name="researchsignaltype",
)
research_verdict_enum = sa.Enum("pass", "hold", "reject", name="researchdecisionverdict")
incident_severity_enum = sa.Enum("low", "medium", "high", "critical", name="incidentseverity")


def upgrade() -> None:
    bind = op.get_bind()
    research_signal_enum.create(bind, checkfirst=True)
    research_verdict_enum.create(bind, checkfirst=True)
    incident_severity_enum.create(bind, checkfirst=True)

    op.create_table(
        "source_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=True),
        sa.Column("evidence_type", sa.String(length=80), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_uri", sa.String(length=500), nullable=True),
        sa.Column("content_excerpt", sa.Text(), nullable=False),
        sa.Column("collected_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_evidence_hypothesis_id", "source_evidence", ["hypothesis_id"])
    op.create_index("ix_source_evidence_run_id", "source_evidence", ["run_id"])

    op.create_table(
        "normalized_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("source_evidence.id"), nullable=False),
        sa.Column("signal_type", research_signal_enum, nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_normalized_signals_hypothesis_id", "normalized_signals", ["hypothesis_id"])
    op.create_index("ix_normalized_signals_evidence_id", "normalized_signals", ["evidence_id"])

    op.create_table(
        "product_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=True),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("score_breakdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_product_scores_hypothesis_id", "product_scores", ["hypothesis_id"])
    op.create_index("ix_product_scores_run_id", "product_scores", ["run_id"])

    op.create_table(
        "decision_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=True),
        sa.Column("verdict", research_verdict_enum, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_decision_cards_hypothesis_id", "decision_cards", ["hypothesis_id"])
    op.create_index("ix_decision_cards_run_id", "decision_cards", ["run_id"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("agent_tasks.id"), nullable=True),
        sa.Column("severity", incident_severity_enum, nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("recovery_action", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_incidents_hypothesis_id", "incidents", ["hypothesis_id"])
    op.create_index("ix_incidents_run_id", "incidents", ["run_id"])
    op.create_index("ix_incidents_task_id", "incidents", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_incidents_task_id", table_name="incidents")
    op.drop_index("ix_incidents_run_id", table_name="incidents")
    op.drop_index("ix_incidents_hypothesis_id", table_name="incidents")
    op.drop_table("incidents")

    op.drop_index("ix_decision_cards_run_id", table_name="decision_cards")
    op.drop_index("ix_decision_cards_hypothesis_id", table_name="decision_cards")
    op.drop_table("decision_cards")

    op.drop_index("ix_product_scores_run_id", table_name="product_scores")
    op.drop_index("ix_product_scores_hypothesis_id", table_name="product_scores")
    op.drop_table("product_scores")

    op.drop_index("ix_normalized_signals_evidence_id", table_name="normalized_signals")
    op.drop_index("ix_normalized_signals_hypothesis_id", table_name="normalized_signals")
    op.drop_table("normalized_signals")

    op.drop_index("ix_source_evidence_run_id", table_name="source_evidence")
    op.drop_index("ix_source_evidence_hypothesis_id", table_name="source_evidence")
    op.drop_table("source_evidence")

    bind = op.get_bind()
    incident_severity_enum.drop(bind, checkfirst=True)
    research_verdict_enum.drop(bind, checkfirst=True)
    research_signal_enum.drop(bind, checkfirst=True)
