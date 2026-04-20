from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DecisionStage, HypothesisStatus


class ProductHypothesis(Base):
    __tablename__ = "product_hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    problem_statement: Mapped[str] = mapped_column(Text)
    target_audience: Mapped[str] = mapped_column(String(200))
    status: Mapped[HypothesisStatus] = mapped_column(
        Enum(HypothesisStatus), default=HypothesisStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product_card: Mapped["ProductCard"] = relationship(back_populates="hypothesis", uselist=False)
    supplier_assessments: Mapped[list["SupplierAssessment"]] = relationship(back_populates="hypothesis")
    competitor_snapshots: Mapped[list["CompetitorSnapshot"]] = relationship(back_populates="hypothesis")
    unit_economics: Mapped["UnitEconomics"] = relationship(back_populates="hypothesis", uselist=False)
    offers: Mapped[list["Offer"]] = relationship(back_populates="hypothesis")
    traffic_tests: Mapped[list["TrafficTest"]] = relationship(back_populates="hypothesis")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="hypothesis")
    artifacts: Mapped[list["ArtifactPackage"]] = relationship(back_populates="hypothesis")
    knowledge_items: Mapped[list["KnowledgeBase"]] = relationship(back_populates="hypothesis")
    final_decision: Mapped["FinalDecision"] = relationship(back_populates="hypothesis", uselist=False)
    postmortem: Mapped["Postmortem"] = relationship(back_populates="hypothesis", uselist=False)


class ProductCard(Base):
    __tablename__ = "product_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"), unique=True)
    product_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(120))
    cost_of_goods: Mapped[float] = mapped_column(Float)
    target_price: Mapped[float] = mapped_column(Float)
    shipping_cost: Mapped[float] = mapped_column(Float)

    problem_or_desire_score: Mapped[int] = mapped_column(Integer)
    visual_potential_score: Mapped[int] = mapped_column(Integer)
    margin_score: Mapped[int] = mapped_column(Integer)
    ad_risk_score: Mapped[int] = mapped_column(Integer)
    logistics_risk_score: Mapped[int] = mapped_column(Integer)

    total_score: Mapped[float] = mapped_column(Float, default=0)
    product_decision: Mapped[str] = mapped_column(String(40), default="reserve")

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="product_card")


class SupplierAssessment(Base):
    __tablename__ = "supplier_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    supplier_name: Mapped[str] = mapped_column(String(200))
    lead_time_days: Mapped[int] = mapped_column(Integer)
    quality_risk_note: Mapped[str] = mapped_column(Text)
    moq_units: Mapped[int] = mapped_column(Integer)
    verified: Mapped[int] = mapped_column(Integer, default=0)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="supplier_assessments")


class CompetitorSnapshot(Base):
    __tablename__ = "competitor_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    competitor_name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float)
    positioning_angle: Mapped[str] = mapped_column(String(200))

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="competitor_snapshots")


class UnitEconomics(Base):
    __tablename__ = "unit_economics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"), unique=True)
    cogs: Mapped[float] = mapped_column(Float)
    shipping_cost: Mapped[float] = mapped_column(Float)
    ad_cost_per_order: Mapped[float] = mapped_column(Float)
    transaction_fee: Mapped[float] = mapped_column(Float)
    selling_price: Mapped[float] = mapped_column(Float)
    contribution_margin: Mapped[float] = mapped_column(Float)
    margin_percent: Mapped[float] = mapped_column(Float)
    break_even_roas: Mapped[float] = mapped_column(Float)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="unit_economics")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    title: Mapped[str] = mapped_column(String(200))
    angle: Mapped[str] = mapped_column(String(200))
    value_proposition: Mapped[str] = mapped_column(Text)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="offers")
    landing_pages: Mapped[list["LandingPage"]] = relationship(back_populates="offer")


class LandingPage(Base):
    __tablename__ = "landing_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"))
    hero_block: Mapped[str] = mapped_column(Text)
    benefits_block: Mapped[str] = mapped_column(Text)
    proof_block: Mapped[str] = mapped_column(Text)
    offer_block: Mapped[str] = mapped_column(Text)
    faq_block: Mapped[str] = mapped_column(Text)
    mobile_ready: Mapped[int] = mapped_column(Integer, default=0)

    offer: Mapped[Offer] = relationship(back_populates="landing_pages")


class Creative(Base):
    __tablename__ = "creatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    traffic_test_id: Mapped[int] = mapped_column(ForeignKey("traffic_tests.id"))
    format: Mapped[str] = mapped_column(String(60))
    angle: Mapped[str] = mapped_column(String(200))
    hook: Mapped[str] = mapped_column(String(200))

    traffic_test: Mapped["TrafficTest"] = relationship(back_populates="creatives")


class TrafficTest(Base):
    __tablename__ = "traffic_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    channel: Mapped[str] = mapped_column(String(100))
    budget: Mapped[float] = mapped_column(Float)
    test_plan: Mapped[str] = mapped_column(Text)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="traffic_tests")
    creatives: Mapped[list[Creative]] = relationship(back_populates="traffic_test")
    metric_snapshots: Mapped[list["MetricSnapshot"]] = relationship(back_populates="traffic_test")


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    traffic_test_id: Mapped[int] = mapped_column(ForeignKey("traffic_tests.id"))
    day_label: Mapped[str] = mapped_column(String(40))
    impressions: Mapped[int] = mapped_column(Integer)
    clicks: Mapped[int] = mapped_column(Integer)
    cpc: Mapped[float] = mapped_column(Float)
    ctr: Mapped[float] = mapped_column(Float)
    cpa: Mapped[float] = mapped_column(Float)
    roas: Mapped[float] = mapped_column(Float)

    traffic_test: Mapped[TrafficTest] = relationship(back_populates="metric_snapshots")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    stage: Mapped[DecisionStage] = mapped_column(Enum(DecisionStage))
    decision_value: Mapped[str] = mapped_column(String(60))
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="decisions")


class ArtifactPackage(Base):
    __tablename__ = "artifact_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    package_type: Mapped[str] = mapped_column(String(80))
    location_uri: Mapped[str] = mapped_column(String(400))
    notes: Mapped[str] = mapped_column(Text)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="artifacts")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"))
    title: Mapped[str] = mapped_column(String(200))
    finding: Mapped[str] = mapped_column(Text)
    reusable_rule: Mapped[str] = mapped_column(Text)
    tag: Mapped[str] = mapped_column(String(80))

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="knowledge_items")


class FinalDecision(Base):
    __tablename__ = "final_decisions"
    __table_args__ = (UniqueConstraint("hypothesis_id", name="uq_final_decision_hypothesis"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"), nullable=False)
    final_outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="final_decision")


class Postmortem(Base):
    __tablename__ = "postmortems"
    __table_args__ = (UniqueConstraint("hypothesis_id", name="uq_postmortem_hypothesis"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("product_hypotheses.id"), nullable=False)
    what_worked: Mapped[str] = mapped_column(Text, nullable=False)
    what_failed: Mapped[str] = mapped_column(Text, nullable=False)
    key_risks: Mapped[str] = mapped_column(Text, nullable=False)
    next_action: Mapped[str] = mapped_column(String(40), nullable=False)
    lessons: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    hypothesis: Mapped[ProductHypothesis] = relationship(back_populates="postmortem")
