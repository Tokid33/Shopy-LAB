"""add traceability fields for agent runs

Revision ID: 0004_agent_traceability
Revises: 0003_agent_foundation
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_agent_traceability"
down_revision = "0003_agent_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("trace_id", sa.String(length=64), nullable=True))
    op.add_column("agent_runs", sa.Column("provider_snapshot", sa.Text(), nullable=True))
    op.add_column("agent_runs", sa.Column("prompt_path", sa.String(length=400), nullable=True))
    op.add_column("agent_runs", sa.Column("prompt_version", sa.String(length=64), nullable=True))
    op.add_column("agent_runs", sa.Column("warnings", sa.Text(), nullable=True))

    op.add_column("agent_artifacts", sa.Column("provider_name", sa.String(length=80), nullable=True))
    op.add_column("agent_artifacts", sa.Column("prompt_path", sa.String(length=400), nullable=True))
    op.add_column("agent_artifacts", sa.Column("trace_id", sa.String(length=64), nullable=True))

    op.execute("UPDATE agent_runs SET trace_id = 'legacy-trace' WHERE trace_id IS NULL")
    op.execute("UPDATE agent_runs SET provider_snapshot = '{}' WHERE provider_snapshot IS NULL")

    with op.batch_alter_table("agent_runs") as batch_op:
        batch_op.alter_column("trace_id", nullable=False)
        batch_op.alter_column("provider_snapshot", nullable=False)


def downgrade() -> None:
    op.drop_column("agent_artifacts", "trace_id")
    op.drop_column("agent_artifacts", "prompt_path")
    op.drop_column("agent_artifacts", "provider_name")

    op.drop_column("agent_runs", "warnings")
    op.drop_column("agent_runs", "prompt_version")
    op.drop_column("agent_runs", "prompt_path")
    op.drop_column("agent_runs", "provider_snapshot")
    op.drop_column("agent_runs", "trace_id")
