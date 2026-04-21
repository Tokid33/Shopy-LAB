"""init mvp schema

Revision ID: 0001_init_mvp
Revises:
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init_mvp"
down_revision = None
branch_labels = None
depends_on = None


hypothesis_status_enum = sa.Enum("draft", "scored", "go", "no_go", name="hypothesisstatus")
decision_stage_enum = sa.Enum("product", "site", "traffic", "final", name="decisionstage")


def upgrade() -> None:
    hypothesis_status_enum.create(op.get_bind(), checkfirst=True)
    decision_stage_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "product_hypotheses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.String(length=200), nullable=False),
        sa.Column("status", hypothesis_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "product_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), unique=True, nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("cost_of_goods", sa.Float(), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=False),
        sa.Column("shipping_cost", sa.Float(), nullable=False),
        sa.Column("problem_or_desire_score", sa.Integer(), nullable=False),
        sa.Column("visual_potential_score", sa.Integer(), nullable=False),
        sa.Column("margin_score", sa.Integer(), nullable=False),
        sa.Column("ad_risk_score", sa.Integer(), nullable=False),
        sa.Column("logistics_risk_score", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("product_decision", sa.String(length=40), nullable=False),
    )

    for table in ["supplier_assessments", "competitor_snapshots", "offers", "traffic_tests", "decisions", "artifact_packages", "knowledge_base"]:
        pass

    op.create_table(
        "supplier_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("supplier_name", sa.String(length=200), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("quality_risk_note", sa.Text(), nullable=False),
        sa.Column("moq_units", sa.Integer(), nullable=False),
        sa.Column("verified", sa.Integer(), nullable=False),
    )

    op.create_table(
        "competitor_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("competitor_name", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("positioning_angle", sa.String(length=200), nullable=False),
    )

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("angle", sa.String(length=200), nullable=False),
        sa.Column("value_proposition", sa.Text(), nullable=False),
    )

    op.create_table(
        "landing_pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("hero_block", sa.Text(), nullable=False),
        sa.Column("benefits_block", sa.Text(), nullable=False),
        sa.Column("proof_block", sa.Text(), nullable=False),
        sa.Column("offer_block", sa.Text(), nullable=False),
        sa.Column("faq_block", sa.Text(), nullable=False),
        sa.Column("mobile_ready", sa.Integer(), nullable=False),
    )

    op.create_table(
        "traffic_tests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("channel", sa.String(length=100), nullable=False),
        sa.Column("budget", sa.Float(), nullable=False),
        sa.Column("test_plan", sa.Text(), nullable=False),
    )

    op.create_table(
        "creatives",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("traffic_test_id", sa.Integer(), sa.ForeignKey("traffic_tests.id"), nullable=False),
        sa.Column("format", sa.String(length=60), nullable=False),
        sa.Column("angle", sa.String(length=200), nullable=False),
        sa.Column("hook", sa.String(length=200), nullable=False),
    )

    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("traffic_test_id", sa.Integer(), sa.ForeignKey("traffic_tests.id"), nullable=False),
        sa.Column("day_label", sa.String(length=40), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("cpc", sa.Float(), nullable=False),
        sa.Column("ctr", sa.Float(), nullable=False),
        sa.Column("cpa", sa.Float(), nullable=False),
        sa.Column("roas", sa.Float(), nullable=False),
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("stage", decision_stage_enum, nullable=False),
        sa.Column("decision_value", sa.String(length=60), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "artifact_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("package_type", sa.String(length=80), nullable=False),
        sa.Column("location_uri", sa.String(length=400), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
    )

    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hypothesis_id", sa.Integer(), sa.ForeignKey("product_hypotheses.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("finding", sa.Text(), nullable=False),
        sa.Column("reusable_rule", sa.Text(), nullable=False),
        sa.Column("tag", sa.String(length=80), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("knowledge_base")
    op.drop_table("artifact_packages")
    op.drop_table("decisions")
    op.drop_table("metric_snapshots")
    op.drop_table("creatives")
    op.drop_table("traffic_tests")
    op.drop_table("landing_pages")
    op.drop_table("offers")
    op.drop_table("competitor_snapshots")
    op.drop_table("supplier_assessments")
    op.drop_table("product_cards")
    op.drop_table("product_hypotheses")

    decision_stage_enum.drop(op.get_bind(), checkfirst=True)
    hypothesis_status_enum.drop(op.get_bind(), checkfirst=True)
