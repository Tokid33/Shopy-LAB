"""add agent foundation tables

Revision ID: 0003_agent_foundation
Revises: 0002_unit_economics_finalization
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_agent_foundation"
down_revision = "0002_unit_economics_finalization"
branch_labels = None
depends_on = None


agent_status_enum = sa.Enum("created", "running", "completed", "failed", name="agentrunstatus")
agent_type_enum = sa.Enum("product_scout", "supplier_check", name="agenttype")


def upgrade() -> None:
    agent_status_enum.create(op.get_bind(), checkfirst=True)
    agent_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=True),
        sa.Column("agent_type", agent_type_enum, nullable=False),
        sa.Column("status", agent_status_enum, nullable=False),
        sa.Column("input_payload", sa.Text(), nullable=False),
        sa.Column("output_payload", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    op.create_table(
        "agent_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("task_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("input_payload", sa.Text(), nullable=False),
        sa.Column("output_payload", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "agent_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("artifact_type", sa.String(length=80), nullable=False),
        sa.Column("content_uri", sa.String(length=400), nullable=True),
        sa.Column("content_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "agent_decision_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("item_ref", sa.String(length=200), nullable=False),
        sa.Column("decision", sa.String(length=60), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("agent_decision_logs")
    op.drop_table("agent_artifacts")
    op.drop_table("agent_tasks")
    op.drop_table("agent_runs")
    agent_type_enum.drop(op.get_bind(), checkfirst=True)
    agent_status_enum.drop(op.get_bind(), checkfirst=True)
