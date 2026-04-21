import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import ProductCard, ProductHypothesis
from app.models.enums import HypothesisStatus
from app.services.cycle_report import (
    HypothesisNotFoundError,
    build_cycle_report,
    export_cycle_report,
    render_cycle_report_markdown,
)
from app.services.workflow import run_demo_cycle


def test_cycle_report_export_smoke(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = run_demo_cycle(db)
        json_path, md_path = export_cycle_report(db, hypothesis.id, output_dir=str(tmp_path))

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["hypothesis_summary"]["status"] == "ok"
    assert data["product_card"]["status"] == "ok"
    assert data["final_decision"]["status"] == "ok"
    assert data["report_meta"]["cycle_completeness"] == "complete"
    assert md_path.exists()


def test_cycle_report_partial_cycle_marks_missing() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        hypothesis = ProductHypothesis(
            title="Partial cycle",
            problem_statement="Need quick validation",
            target_audience="Busy parents",
            status=HypothesisStatus.draft,
        )
        db.add(hypothesis)
        db.flush()

        db.add(
            ProductCard(
                hypothesis_id=hypothesis.id,
                product_name="Mini organizer",
                category="Home",
                cost_of_goods=8,
                target_price=24,
                shipping_cost=3,
                problem_or_desire_score=7,
                visual_potential_score=6,
                margin_score=6,
                ad_risk_score=5,
                logistics_risk_score=6,
                total_score=63,
                product_decision="reserve",
            )
        )
        db.commit()

        report = build_cycle_report(db, hypothesis.id)
        markdown = render_cycle_report_markdown(report)

    assert report["product_card"]["status"] == "ok"
    assert report["offer"]["status"] == "missing"
    assert report["traffic_test"]["status"] == "missing"
    assert report["report_meta"]["cycle_completeness"] == "partial"
    assert "MISSING: no data recorded for this section." in markdown


def test_cycle_report_missing_hypothesis_id() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        with pytest.raises(HypothesisNotFoundError):
            build_cycle_report(db, 999)
