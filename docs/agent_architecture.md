# Agent Architecture (v0 foundation)

## Принципы
1. Backward-compatible: существующий MVP не ломается.
2. Thin orchestration: без Celery/Redis/Kafka на этом этапе.
3. Adapter-first: провайдеры заданы интерфейсами.

## Слои
- `app/services/agents/providers.py`
  - Контракты: `SearchProvider`, `WebPageFetcher`, `LLMExtractor`
  - Demo adapters: fake implementations

- `app/services/agents/services.py`
  - `ProductScoutAgentService`
  - `SupplierCheckAgentService`
  - orchestration + сохранение результатов

- `app/services/agents/runtime.py`
  - единые helper-функции для записи `AgentRun` / tasks / artifacts / decision logs

## Data model
- `AgentRun`: lifecycle run'а агента
- `AgentTask`: подзадачи внутри run
- `AgentArtifact`: сохранённые артефакты
- `AgentDecisionLog`: объяснимые решения по элементам

## Почему это agent-ready
- Есть единый lifecycle запуска
- Есть сохраняемая история решений
- Есть точки расширения под реальные провайдеры
- Нет привязки к конкретному внешнему API
