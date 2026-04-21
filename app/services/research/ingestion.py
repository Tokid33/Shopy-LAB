from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, NormalizedSignal, SourceEvidence
from app.models.enums import ResearchSignalType


@dataclass
class IngestionSummary:
    created_evidence_id: int
    minimal_signal_pack_ready: bool


@dataclass
class NormalizationSummary:
    run_id: int
    created_signals: int
    minimal_signal_pack_ready: bool


class ResearchIngestionService:
    REQUIRED_EVIDENCE_TYPES = {"market", "voc", "supplier"}

    def __init__(self, db: Session):
        self.db = db

    def save_evidence(
        self,
        run_id: int,
        evidence_type: str,
        source_name: str,
        content_excerpt: str,
        source_uri: str | None = None,
    ) -> IngestionSummary:
        run = self.db.get(AgentRun, run_id)
        if not run:
            raise ValueError(f"Research run {run_id} not found")
        if run.hypothesis_id is None:
            raise ValueError(f"Research run {run_id} has no hypothesis")

        evidence = SourceEvidence(
            hypothesis_id=run.hypothesis_id,
            run_id=run.id,
            evidence_type=evidence_type,
            source_name=source_name,
            source_uri=source_uri,
            content_excerpt=content_excerpt,
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        return IngestionSummary(
            created_evidence_id=evidence.id,
            minimal_signal_pack_ready=self._has_minimal_pack(run.id),
        )

    def normalize_run_evidence(self, run_id: int) -> NormalizationSummary:
        run = self.db.get(AgentRun, run_id)
        if not run:
            raise ValueError(f"Research run {run_id} not found")
        if run.hypothesis_id is None:
            raise ValueError(f"Research run {run_id} has no hypothesis")

        stmt = select(SourceEvidence).where(SourceEvidence.run_id == run_id)
        evidences = self.db.scalars(stmt).all()

        created = 0
        for evidence in evidences:
            if evidence.signals:
                continue
            signal = NormalizedSignal(
                hypothesis_id=run.hypothesis_id,
                evidence_id=evidence.id,
                signal_type=self._map_signal_type(evidence.evidence_type),
                value=self._estimate_value(evidence.content_excerpt),
                confidence=self._estimate_confidence(evidence.content_excerpt),
                rationale=f"Auto-normalized from {evidence.evidence_type}:{evidence.source_name}",
            )
            self.db.add(signal)
            created += 1

        self.db.commit()
        return NormalizationSummary(
            run_id=run_id,
            created_signals=created,
            minimal_signal_pack_ready=self._has_minimal_pack(run_id),
        )

    def _has_minimal_pack(self, run_id: int) -> bool:
        stmt = select(SourceEvidence.evidence_type).where(SourceEvidence.run_id == run_id)
        evidence_types = set(self.db.scalars(stmt).all())
        return self.REQUIRED_EVIDENCE_TYPES.issubset(evidence_types)

    @staticmethod
    def _map_signal_type(evidence_type: str) -> ResearchSignalType:
        mapping = {
            "market": ResearchSignalType.market_competition,
            "voc": ResearchSignalType.problem_severity,
            "supplier": ResearchSignalType.supplier_reliability,
            "economics": ResearchSignalType.unit_economics,
        }
        return mapping.get(evidence_type, ResearchSignalType.willingness_to_pay)

    @staticmethod
    def _estimate_value(text: str) -> float:
        return min(1.0, max(0.1, len(text) / 280.0))

    @staticmethod
    def _estimate_confidence(text: str) -> float:
        return min(0.95, max(0.35, len(text) / 500.0))
