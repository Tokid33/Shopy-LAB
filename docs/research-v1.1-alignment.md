# Research v1.1 Artifact Alignment (Step 1)

## Goal
Create an explicit alignment checkpoint between the expected **research-stage** architecture and the current codebase before schema/API changes.

## Source-of-truth status
The expected artifact directory mentioned by product requirements is:

- `диаграммы/артефакты v1.1 reserch`

As of **2026-04-21**, this path is not present in the repository tree.

### Verification commands
- `find .. -name 'AGENTS.md' -print`
- `rg --files`
- `find . -maxdepth 3 -type d | sed -n '1,200p'`

Because the v1.1 artifact directory is missing, this document records a **provisional mapping** based on the current implementation and docs.

## Provisional entity mapping

| Target (research v1.1) | Current implementation | Gap / notes |
|---|---|---|
| `product_hypothesis` | `ProductHypothesis` (`app/models/entities.py`) | Exists and can be reused. |
| `agent_run` | `AgentRun` (`app/models/entities.py`) | Exists and can be reused for research runs. |
| `agent_task` | `AgentTask` (`app/models/entities.py`) | Exists; needs planner semantics for scout/voc/supplier/decision. |
| `source_evidence` | No dedicated table | Missing; must be added with source metadata + traceability. |
| `normalized_signal` | No dedicated table | Missing; must be added and linked to evidence and hypothesis. |
| `product_score` | `ProductCard.score`/`ProductCard.confidence` | Similar data exists, but not as standalone research-stage scoring artifact. |
| `decision_card` | `FinalDecision` | Similar outcome exists, but schema and lifecycle differ from requested research-stage decision card. |
| `incident` | No dedicated table | Missing; needed for run-level and task-level failure/risk handling. |

## API alignment snapshot

Current API contains health, cycle/demo, and agent runtime endpoints (`app/api/routes.py`).

Required for research v1.1 (planned):

- `POST /hypotheses`
- `GET/PATCH /hypotheses/{id}`
- `POST /hypotheses/{id}/research-runs`
- `GET /research-runs/{run_id}`
- `GET /hypotheses/{id}/decision-card`

Status: **not implemented** as dedicated research-stage contracts.

## Decision for Step 1

1. Freeze this alignment baseline.
2. Keep existing MVP flow intact.
3. Introduce research-stage entities and endpoints in parallel (Step 2+).
4. Replace this provisional mapping with exact mapping once the missing v1.1 artifact folder is added.

## Exit criteria for Step 1

- [x] Current-vs-target mapping documented.
- [x] Missing source-of-truth artifact path recorded.
- [x] Implementation order constraint captured (non-breaking parallel addition).

## Next step (Step 2)

Add schema foundation for missing research entities:

- `source_evidence`
- `normalized_signal`
- `product_score`
- `decision_card`
- `incident`

with migrations, indexes, and foreign keys.
