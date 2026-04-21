# Domain Model (MVP)

## Основные сущности
- `ProductHypothesis`: корневая сущность цикла, статус прогресса.
- `ProductCard`: оценка товара и scoring.
- `SupplierAssessment`: проверка поставщика.
- `CompetitorSnapshot`: срез конкурентного окружения.
- `Offer`: оффер и угол подачи.
- `LandingPage`: контентные блоки LP и mobile readiness.
- `Creative`: рекламная единица для теста.
- `TrafficTest`: параметры теста трафика.
- `MetricSnapshot`: метрики по дням/срезам.
- `Decision`: решение на этапах (product/site/traffic/final).
- `ArtifactPackage`: ссылки на собранные артефакты.
- `KnowledgeBase`: знания и переиспользуемые правила.
- `UnitEconomics`: юнит-экономика и порог окупаемости рекламы.
- `FinalDecision`: строгое финальное решение цикла (one per hypothesis).
- `Postmortem`: структурированный разбор цикла (one per hypothesis).
- `AgentRun`, `AgentTask`, `AgentArtifact`, `AgentDecisionLog`: трассируемый агентный runtime.

## Связи
- `ProductHypothesis` 1—1 `ProductCard`
- `ProductHypothesis` 1—N `SupplierAssessment`, `CompetitorSnapshot`, `Offer`, `TrafficTest`, `Decision`, `ArtifactPackage`, `KnowledgeBase`
- `Offer` 1—N `LandingPage`
- `TrafficTest` 1—N `Creative`, `MetricSnapshot`
- `ProductHypothesis` 1—1 `UnitEconomics`, `FinalDecision`, `Postmortem`
- `ProductHypothesis` 1—N `AgentRun`

## Lifecycle discipline
В v1.0 модель включает lifecycle states для:
- `ProductHypothesis`
- `LandingPage`
- `TrafficTest`
- `FinalDecision`

См. `docs/state-machine.md`.
