"""add lifecycle states and invariants fields

Revision ID: 0005_state_machine_fields
Revises: 0004_agent_traceability
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_state_machine_fields"
down_revision = "0004_agent_traceability"
branch_labels = None
depends_on = None


hypothesis_lifecycle_enum = sa.Enum(
    "product_discovery",
    "site_ready",
    "traffic_running",
    "traffic_completed",
    "finalized",
    name="hypothesislifecyclestate",
)
landing_state_enum = sa.Enum("draft", "ready_for_traffic", name="landingpagestate")
traffic_state_enum = sa.Enum("planned", "running", "completed", name="trafficteststate")
final_decision_state_enum = sa.Enum("recorded", name="finaldecisionstate")


def upgrade() -> None:
    bind = op.get_bind()
    hypothesis_lifecycle_enum.create(bind, checkfirst=True)
    landing_state_enum.create(bind, checkfirst=True)
    traffic_state_enum.create(bind, checkfirst=True)
    final_decision_state_enum.create(bind, checkfirst=True)

    op.add_column("product_hypotheses", sa.Column("lifecycle_state", hypothesis_lifecycle_enum, nullable=True))
    op.add_column("landing_pages", sa.Column("lifecycle_state", landing_state_enum, nullable=True))
    op.add_column("traffic_tests", sa.Column("lifecycle_state", traffic_state_enum, nullable=True))
    op.add_column("final_decisions", sa.Column("lifecycle_state", final_decision_state_enum, nullable=True))

    op.execute("UPDATE product_hypotheses SET lifecycle_state = 'product_discovery' WHERE lifecycle_state IS NULL")
    op.execute("UPDATE landing_pages SET lifecycle_state = 'draft' WHERE lifecycle_state IS NULL")
    op.execute("UPDATE traffic_tests SET lifecycle_state = 'planned' WHERE lifecycle_state IS NULL")
    op.execute("UPDATE final_decisions SET lifecycle_state = 'recorded' WHERE lifecycle_state IS NULL")

    with op.batch_alter_table("product_hypotheses") as batch_op:
        batch_op.alter_column("lifecycle_state", nullable=False)
    with op.batch_alter_table("landing_pages") as batch_op:
        batch_op.alter_column("lifecycle_state", nullable=False)
    with op.batch_alter_table("traffic_tests") as batch_op:
        batch_op.alter_column("lifecycle_state", nullable=False)
    with op.batch_alter_table("final_decisions") as batch_op:
        batch_op.alter_column("lifecycle_state", nullable=False)


def downgrade() -> None:
    op.drop_column("final_decisions", "lifecycle_state")
    op.drop_column("traffic_tests", "lifecycle_state")
    op.drop_column("landing_pages", "lifecycle_state")
    op.drop_column("product_hypotheses", "lifecycle_state")

    bind = op.get_bind()
    final_decision_state_enum.drop(bind, checkfirst=True)
    traffic_state_enum.drop(bind, checkfirst=True)
    landing_state_enum.drop(bind, checkfirst=True)
    hypothesis_lifecycle_enum.drop(bind, checkfirst=True)
