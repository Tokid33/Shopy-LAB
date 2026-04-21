"""add unit economics and strict finalization

Revision ID: 0002_unit_economics_finalization
Revises: 0001_init_mvp
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_unit_economics_finalization"
down_revision = "0001_init_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "unit_economics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False, unique=True),
        sa.Column("cogs", sa.Float(), nullable=False),
        sa.Column("shipping_cost", sa.Float(), nullable=False),
        sa.Column("ad_cost_per_order", sa.Float(), nullable=False),
        sa.Column("transaction_fee", sa.Float(), nullable=False),
        sa.Column("selling_price", sa.Float(), nullable=False),
        sa.Column("contribution_margin", sa.Float(), nullable=False),
        sa.Column("margin_percent", sa.Float(), nullable=False),
        sa.Column("break_even_roas", sa.Float(), nullable=False),
    )

    op.create_table(
        "final_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("final_outcome", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("hypothesis_id", name="uq_final_decision_hypothesis"),
    )

    op.create_table(
        "postmortems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("what_worked", sa.Text(), nullable=False),
        sa.Column("what_failed", sa.Text(), nullable=False),
        sa.Column("key_risks", sa.Text(), nullable=False),
        sa.Column("next_action", sa.String(length=40), nullable=False),
        sa.Column("lessons", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("hypothesis_id", name="uq_postmortem_hypothesis"),
    )


def downgrade() -> None:
    op.drop_table("postmortems")
    op.drop_table("final_decisions")
    op.drop_table("unit_economics")
