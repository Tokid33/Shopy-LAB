from sqlalchemy.orm import Session

from app.models import (
    ArtifactPackage,
    CompetitorSnapshot,
    Creative,
    Decision,
    KnowledgeBase,
    LandingPage,
    MetricSnapshot,
    Offer,
    ProductCard,
    ProductHypothesis,
    SupplierAssessment,
    TrafficTest,
)
from app.models.enums import DecisionStage, HypothesisStatus
from app.schemas.hypothesis import ProductCardCreate, ProductHypothesisCreate
from app.services.scoring import score_product


def run_demo_cycle(db: Session) -> ProductHypothesis:
    hypothesis = ProductHypothesis(
        **ProductHypothesisCreate(
            title="Portable blender for office workers",
            problem_statement="Healthy snacks at work are inconvenient",
            target_audience="Office workers 24-40",
        ).model_dump()
    )
    db.add(hypothesis)
    db.flush()

    card_payload = ProductCardCreate(
        product_name="BlendGo Mini",
        category="Kitchen",
        cost_of_goods=12,
        target_price=39,
        shipping_cost=4,
        problem_or_desire_score=8,
        visual_potential_score=8,
        margin_score=7,
        ad_risk_score=8,
        logistics_risk_score=8,
    )
    score = score_product(card_payload)

    card = ProductCard(hypothesis_id=hypothesis.id, **card_payload.model_dump(), total_score=score.total_score, product_decision=score.decision)
    hypothesis.status = HypothesisStatus.scored if score.decision != "reject" else HypothesisStatus.no_go
    db.add(card)

    db.add(
        Decision(
            hypothesis_id=hypothesis.id,
            stage=DecisionStage.product,
            decision_value=score.decision,
            rationale=score.explanation,
        )
    )

    db.add(
        SupplierAssessment(
            hypothesis_id=hypothesis.id,
            supplier_name="Shenzhen HomeTech Co.",
            lead_time_days=12,
            quality_risk_note="Pre-shipment sample requested",
            moq_units=200,
            verified=1,
        )
    )

    competitors = [
        CompetitorSnapshot(
            hypothesis_id=hypothesis.id,
            competitor_name=f"Competitor {i+1}",
            url=f"https://example.com/c{i+1}",
            price=34 + i,
            positioning_angle="Healthy lifestyle",
        )
        for i in range(5)
    ]
    db.add_all(competitors)

    if score.decision == "shortlist":
        hypothesis.status = HypothesisStatus.go

        offer = Offer(
            hypothesis_id=hypothesis.id,
            title="Blend anywhere in 30 seconds",
            angle="Convenience for office routine",
            value_proposition="Portable blender with USB-C charge and easy cleaning",
        )
        db.add(offer)
        db.flush()

        db.add(
            LandingPage(
                offer_id=offer.id,
                hero_block="Fresh smoothie at your desk",
                benefits_block="Fast blend, compact, rechargeable",
                proof_block="UGC demos + before/after routine",
                offer_block="39 USD + free shaker",
                faq_block="Shipping, warranty, battery",
                mobile_ready=1,
            )
        )

        traffic = TrafficTest(
            hypothesis_id=hypothesis.id,
            channel="Meta Ads",
            budget=300,
            test_plan="3 creatives x 2 angles x 3 days",
        )
        db.add(traffic)
        db.flush()

        db.add_all(
            [
                Creative(traffic_test_id=traffic.id, format="video", angle="time-saving", hook="30 sec blend"),
                Creative(traffic_test_id=traffic.id, format="video", angle="healthy", hook="No sugar office snack"),
                Creative(traffic_test_id=traffic.id, format="image", angle="portability", hook="Fits any bag"),
            ]
        )

        db.add_all(
            [
                MetricSnapshot(
                    traffic_test_id=traffic.id,
                    day_label="day_1",
                    impressions=12000,
                    clicks=420,
                    cpc=0.71,
                    ctr=3.5,
                    cpa=18.2,
                    roas=1.4,
                ),
                MetricSnapshot(
                    traffic_test_id=traffic.id,
                    day_label="day_2",
                    impressions=13200,
                    clicks=480,
                    cpc=0.69,
                    ctr=3.64,
                    cpa=16.9,
                    roas=1.7,
                ),
            ]
        )

        db.add(
            Decision(
                hypothesis_id=hypothesis.id,
                stage=DecisionStage.traffic,
                decision_value="iterate",
                rationale="ROAS improving but below scale threshold 2.0",
            )
        )

        db.add(
            ArtifactPackage(
                hypothesis_id=hypothesis.id,
                package_type="media_pack",
                location_uri="artifacts/blendgo/media-pack-v1.zip",
                notes="3 creatives + LP screenshots",
            )
        )
        db.add(
            KnowledgeBase(
                hypothesis_id=hypothesis.id,
                title="Office convenience angle works best",
                finding="Time-saving angle generated highest CTR",
                reusable_rule="For office audience, lead with routine friction",
                tag="angle-testing",
            )
        )

    db.commit()
    db.refresh(hypothesis)
    return hypothesis
