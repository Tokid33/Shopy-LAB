from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DecisionCard, Incident, NormalizedSignal, ProductHypothesis, ProductScore, SourceEvidence
from app.models.enums import (
    HypothesisStatus,
    IncidentSeverity,
    ResearchDecisionVerdict,
    ResearchSignalType,
)


@dataclass
class EvaluationSummary:
    hypothesis_id: int
    run_id: int
    verdict: ResearchDecisionVerdict
    score_value: float
    confidence: float
    rationale: str
    red_flags: list[str]


class ResearchDecisionService:
    REQUIRED_SIGNAL_TYPES = {
        ResearchSignalType.market_competition,
        ResearchSignalType.problem_severity,
        ResearchSignalType.supplier_reliability,
        ResearchSignalType.unit_economics,
    }

    WEIGHTS = {
        ResearchSignalType.problem_severity: 0.20,
        ResearchSignalType.willingness_to_pay: 0.15,
        ResearchSignalType.market_competition: 0.15,
        ResearchSignalType.supplier_reliability: 0.15,
        ResearchSignalType.unit_economics: 0.20,
        ResearchSignalType.policy_risk: 0.15,
    }

    def __init__(self, db: Session):
        self.db = db

    def evaluate_run(self, run_id: int) -> EvaluationSummary:
        signals = self._get_run_signals(run_id)
        if not signals:
            raise ValueError(f"No normalized signals found for run {run_id}")

        hypothesis_id = signals[0].hypothesis_id
        hypothesis = self.db.get(ProductHypothesis, hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        missing = self._missing_required_signals(signals)
        if missing:
            rationale = f"Missing mandatory signals: {', '.join(sorted([item.value for item in missing]))}"
            summary = self._persist_decision(
                hypothesis=hypothesis,
                run_id=run_id,
                verdict=ResearchDecisionVerdict.hold,
                score_value=0.0,
                confidence=0.35,
                rationale=rationale,
                breakdown={"missing_signals": [item.value for item in missing]},
                red_flags=["missing_mandatory_signals"],
            )
            self._create_incident(
                hypothesis_id=hypothesis_id,
                run_id=run_id,
                severity=IncidentSeverity.medium,
                code="missing_data",
                message=rationale,
                recovery_action="create_retry_tasks_with_alternative_sources",
            )
            self.db.commit()
            return summary

        score_value, confidence, breakdown = self._compute_score(signals)
        red_flags = self._evaluate_red_flags(signals)

        if "compliance_risk" in red_flags:
            verdict = ResearchDecisionVerdict.reject
            rationale = "Critical compliance risk detected"
        elif "supplier_unreliable" in red_flags:
            verdict = ResearchDecisionVerdict.reject
            rationale = "Supplier reliability below floor"
        elif "margin_too_low" in red_flags:
            verdict = ResearchDecisionVerdict.reject
            rationale = "Unit economics below minimum floor"
        elif confidence < 0.45:
            verdict = ResearchDecisionVerdict.hold
            rationale = "Confidence below threshold"
        elif score_value >= 0.70:
            verdict = ResearchDecisionVerdict.pass_
            rationale = "Score above pass threshold"
        elif score_value >= 0.55:
            verdict = ResearchDecisionVerdict.hold
            rationale = "Score in hold band; collect more evidence"
        else:
            verdict = ResearchDecisionVerdict.reject
            rationale = "Score below hold threshold"

        summary = self._persist_decision(
            hypothesis=hypothesis,
            run_id=run_id,
            verdict=verdict,
            score_value=score_value,
            confidence=confidence,
            rationale=rationale,
            breakdown=breakdown,
            red_flags=red_flags,
        )

        if red_flags:
            self._create_incident(
                hypothesis_id=hypothesis_id,
                run_id=run_id,
                severity=IncidentSeverity.high,
                code="critical_risk" if verdict == ResearchDecisionVerdict.reject else "signal_conflict",
                message=f"Red flags: {', '.join(red_flags)}",
                recovery_action="manual_review_or_additional_evidence",
            )

        self.db.commit()
        return summary

    def _get_run_signals(self, run_id: int) -> list[NormalizedSignal]:
        stmt = (
            select(NormalizedSignal)
            .join(SourceEvidence, SourceEvidence.id == NormalizedSignal.evidence_id)
            .where(SourceEvidence.run_id == run_id)
        )
        return self.db.scalars(stmt).all()

    def _missing_required_signals(self, signals: list[NormalizedSignal]) -> set[ResearchSignalType]:
        present = {signal.signal_type for signal in signals}
        return self.REQUIRED_SIGNAL_TYPES - present

    def _compute_score(self, signals: list[NormalizedSignal]) -> tuple[float, float, dict[str, float]]:
        grouped: dict[ResearchSignalType, list[NormalizedSignal]] = {}
        for signal in signals:
            grouped.setdefault(signal.signal_type, []).append(signal)

        weighted_score = 0.0
        total_weight = 0.0
        confidence_values: list[float] = []
        breakdown: dict[str, float] = {}

        for signal_type, signals_for_type in grouped.items():
            avg_value = sum(item.value for item in signals_for_type) / len(signals_for_type)
            avg_conf = sum(item.confidence for item in signals_for_type) / len(signals_for_type)
            weight = self.WEIGHTS.get(signal_type, 0.10)
            weighted_score += avg_value * weight
            total_weight += weight
            confidence_values.append(avg_conf)
            breakdown[signal_type.value] = round(avg_value, 4)

        final_score = weighted_score / total_weight if total_weight else 0.0
        confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        return round(final_score, 4), round(confidence, 4), breakdown

    @staticmethod
    def _evaluate_red_flags(signals: list[NormalizedSignal]) -> list[str]:
        red_flags: list[str] = []
        for signal in signals:
            if signal.signal_type == ResearchSignalType.policy_risk and signal.value >= 0.75:
                red_flags.append("compliance_risk")
            if signal.signal_type == ResearchSignalType.supplier_reliability and signal.value < 0.25:
                red_flags.append("supplier_unreliable")
            if signal.signal_type == ResearchSignalType.unit_economics and signal.value < 0.30:
                red_flags.append("margin_too_low")
        return sorted(set(red_flags))

    def _persist_decision(
        self,
        hypothesis: ProductHypothesis,
        run_id: int,
        verdict: ResearchDecisionVerdict,
        score_value: float,
        confidence: float,
        rationale: str,
        breakdown: dict,
        red_flags: list[str],
    ) -> EvaluationSummary:
        score = ProductScore(
            hypothesis_id=hypothesis.id,
            run_id=run_id,
            score_value=score_value,
            confidence=confidence,
            score_breakdown=str({"signals": breakdown, "red_flags": red_flags}),
        )
        self.db.add(score)

        card = DecisionCard(
            hypothesis_id=hypothesis.id,
            run_id=run_id,
            verdict=verdict,
            confidence=confidence,
            rationale=rationale,
        )
        self.db.add(card)

        if verdict == ResearchDecisionVerdict.pass_:
            hypothesis.status = HypothesisStatus.go
        elif verdict == ResearchDecisionVerdict.reject:
            hypothesis.status = HypothesisStatus.no_go
        else:
            hypothesis.status = HypothesisStatus.scored

        self.db.add(hypothesis)

        return EvaluationSummary(
            hypothesis_id=hypothesis.id,
            run_id=run_id,
            verdict=verdict,
            score_value=score_value,
            confidence=confidence,
            rationale=rationale,
            red_flags=red_flags,
        )

    def _create_incident(
        self,
        hypothesis_id: int,
        run_id: int,
        severity: IncidentSeverity,
        code: str,
        message: str,
        recovery_action: str,
    ) -> None:
        incident = Incident(
            hypothesis_id=hypothesis_id,
            run_id=run_id,
            task_id=None,
            severity=severity,
            code=code,
            message=message,
            recovery_action=recovery_action,
        )
        self.db.add(incident)
