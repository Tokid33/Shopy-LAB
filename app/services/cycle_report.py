import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ProductHypothesis


class HypothesisNotFoundError(ValueError):
    pass


def _as_dict(model, fields: list[str]) -> dict:
    if model is None:
        return {"status": "missing", "data": None}
    return {"status": "ok", "data": {field: getattr(model, field) for field in fields}}


def build_cycle_report(db: Session, hypothesis_id: int) -> dict:
    hypothesis = db.get(ProductHypothesis, hypothesis_id)
    if not hypothesis:
        raise HypothesisNotFoundError(f"Hypothesis with id={hypothesis_id} not found")

    product_card_payload = _as_dict(
        hypothesis.product_card,
        [
            "product_name",
            "category",
            "cost_of_goods",
            "target_price",
            "shipping_cost",
            "problem_or_desire_score",
            "visual_potential_score",
            "margin_score",
            "ad_risk_score",
            "logistics_risk_score",
            "total_score",
            "product_decision",
        ],
    )

    scoring_result = {
        "status": "ok" if hypothesis.product_card else "missing",
        "data": {
            "total_score": hypothesis.product_card.total_score,
            "decision": hypothesis.product_card.product_decision,
            "component_scores": {
                "problem_or_desire_score": hypothesis.product_card.problem_or_desire_score,
                "visual_potential_score": hypothesis.product_card.visual_potential_score,
                "margin_score": hypothesis.product_card.margin_score,
                "ad_risk_score": hypothesis.product_card.ad_risk_score,
                "logistics_risk_score": hypothesis.product_card.logistics_risk_score,
            },
        }
        if hypothesis.product_card
        else None,
    }

    first_offer = hypothesis.offers[0] if hypothesis.offers else None
    first_traffic_test = hypothesis.traffic_tests[0] if hypothesis.traffic_tests else None

    report = {
        "report_meta": {
            "hypothesis_id": hypothesis.id,
            "report_version": "v0.2",
            "generated_for_status": hypothesis.status.value,
        },
        "hypothesis_summary": {
            "status": "ok",
            "data": {
                "id": hypothesis.id,
                "title": hypothesis.title,
                "problem_statement": hypothesis.problem_statement,
                "target_audience": hypothesis.target_audience,
                "status": hypothesis.status.value,
                "created_at": hypothesis.created_at.isoformat() if hypothesis.created_at else None,
            },
        },
        "product_card": product_card_payload,
        "scoring_result": scoring_result,
        "supplier_assessment": {
            "status": "ok" if hypothesis.supplier_assessments else "missing",
            "data": [
                {
                    "supplier_name": s.supplier_name,
                    "lead_time_days": s.lead_time_days,
                    "quality_risk_note": s.quality_risk_note,
                    "moq_units": s.moq_units,
                    "verified": bool(s.verified),
                }
                for s in hypothesis.supplier_assessments
            ],
        },
        "competitor_snapshots": {
            "status": "ok" if hypothesis.competitor_snapshots else "missing",
            "data": [
                {
                    "competitor_name": c.competitor_name,
                    "url": c.url,
                    "price": c.price,
                    "positioning_angle": c.positioning_angle,
                }
                for c in hypothesis.competitor_snapshots
            ],
        },
        "unit_economics": _as_dict(
            hypothesis.unit_economics,
            [
                "cogs",
                "shipping_cost",
                "ad_cost_per_order",
                "transaction_fee",
                "selling_price",
                "contribution_margin",
                "margin_percent",
                "break_even_roas",
            ],
        ),
        "offer": _as_dict(first_offer, ["title", "angle", "value_proposition"]),
        "landing_page": {
            "status": "ok" if first_offer and first_offer.landing_pages else "missing",
            "data": [
                {
                    "hero_block": l.hero_block,
                    "benefits_block": l.benefits_block,
                    "proof_block": l.proof_block,
                    "offer_block": l.offer_block,
                    "faq_block": l.faq_block,
                    "mobile_ready": bool(l.mobile_ready),
                }
                for l in (first_offer.landing_pages if first_offer else [])
            ],
        },
        "creatives": {
            "status": "ok" if first_traffic_test and first_traffic_test.creatives else "missing",
            "data": [
                {"format": cr.format, "angle": cr.angle, "hook": cr.hook}
                for cr in (first_traffic_test.creatives if first_traffic_test else [])
            ],
        },
        "traffic_test": _as_dict(first_traffic_test, ["channel", "budget", "test_plan"]),
        "metric_snapshots": {
            "status": "ok" if first_traffic_test and first_traffic_test.metric_snapshots else "missing",
            "data": [
                {
                    "day_label": m.day_label,
                    "impressions": m.impressions,
                    "clicks": m.clicks,
                    "cpc": m.cpc,
                    "ctr": m.ctr,
                    "cpa": m.cpa,
                    "roas": m.roas,
                }
                for m in (first_traffic_test.metric_snapshots if first_traffic_test else [])
            ],
        },
        "final_decision": _as_dict(
            hypothesis.final_decision,
            ["final_outcome", "confidence", "rationale", "owner", "created_at"],
        ),
        "postmortem": _as_dict(
            hypothesis.postmortem,
            ["what_worked", "what_failed", "key_risks", "next_action", "lessons", "created_at"],
        ),
        "artifact_summary": {
            "status": "ok" if hypothesis.artifacts else "missing",
            "data": {
                "count": len(hypothesis.artifacts),
                "items": [
                    {
                        "package_type": a.package_type,
                        "location_uri": a.location_uri,
                        "notes": a.notes,
                    }
                    for a in hypothesis.artifacts
                ],
            },
        },
        "knowledge_summary": {
            "status": "ok" if hypothesis.knowledge_items else "missing",
            "data": {
                "count": len(hypothesis.knowledge_items),
                "items": [
                    {
                        "title": k.title,
                        "finding": k.finding,
                        "reusable_rule": k.reusable_rule,
                        "tag": k.tag,
                    }
                    for k in hypothesis.knowledge_items
                ],
            },
        },
    }

    return report


def render_cycle_report_markdown(report: dict) -> str:
    lines = [
        f"# Cycle Report — Hypothesis #{report['report_meta']['hypothesis_id']}",
        "",
        f"- Report version: {report['report_meta']['report_version']}",
        f"- Current status: {report['report_meta']['generated_for_status']}",
        "",
    ]

    for section_name, section_data in report.items():
        if section_name == "report_meta":
            continue
        lines.append(f"## {section_name}")
        if section_data["status"] == "missing":
            lines.append("MISSING: no data recorded for this section.")
            lines.append("")
            continue
        lines.append("```json")
        lines.append(json.dumps(section_data["data"], ensure_ascii=False, indent=2, default=str))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def export_cycle_report(db: Session, hypothesis_id: int, output_dir: str = "artifacts/reports") -> tuple[Path, Path]:
    report = build_cycle_report(db, hypothesis_id)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"cycle_report_{hypothesis_id}.json"
    md_path = out_dir / f"cycle_report_{hypothesis_id}.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_cycle_report_markdown(report), encoding="utf-8")

    return json_path, md_path
