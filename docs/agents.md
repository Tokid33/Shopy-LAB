# Agents Layer (Demo/Foundation)

## Зачем добавлен агентный слой
MVP уже умеет проходить цикл вручную/скриптом. Новый слой добавляет управляемые agent-runs,
чтобы в будущем подключить реальные web/search/LLM адаптеры без перестройки ядра.

## Какие роли реализованы
- Product Scout Agent (`product_scout`)
- Supplier Check Agent (`supplier_check`)

## Demo/mock режим
Сейчас используются fake adapters:
- `FakeSearchProvider`
- `FakeWebPageFetcher`
- `FakeLLMExtractor`

Это позволяет запускать агентов локально без ключей и внешних API.

## API endpoints
- `POST /agents/product-scout/run`
- `POST /agents/supplier-check/run`
- `GET /agents/runs/{run_id}`

## Что хранится в БД
- `AgentRun`
- `AgentTask`
- `AgentArtifact`
- `AgentDecisionLog`

## Следующий шаг
Подключить real adapters (например, search API + page fetch + LLM extraction), сохраняя те же интерфейсы.
