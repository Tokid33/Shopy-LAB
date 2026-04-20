# Agents Layer (usable execution v1)

## Режимы запуска
- **mock mode** (по умолчанию): безопасный, без внешних ключей.
- **real mode**: ограниченный реальный execution path через provider adapters.

## Execution config (env)
- `AGENT_MODE=mock|real`
- `SEARCH_PROVIDER=fake|brave|serpapi`
- `FETCH_PROVIDER=fake|http`
- `LLM_PROVIDER=fake|openai_compatible`
- `LLM_MODEL`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `SEARCH_API_KEY`
- `REQUEST_TIMEOUT_SECONDS`
- `MAX_SEARCH_RESULTS`
- `MAX_FETCH_PAGES`
- `MAX_PAGE_TEXT_CHARS`
- `ENABLE_PROMPT_TRACING`
- `ENABLE_RAW_ARTIFACT_CAPTURE`

## Provider health
Endpoint: `GET /agents/providers/health`

Возвращает:
- активный mode
- выбранные провайдеры
- доступные провайдеры
- отсутствующие env
- готовность real mode

## Product Scout flow
1. Генерирует search queries по `market + categories`.
2. Делает search и dedup ссылок.
3. Fetch страниц (ограничения по timeout/size/pages).
4. LLM extraction в structured candidate.
5. Quality gates.
6. Scoring existing engine.
7. Запись AgentRun/Task/Artifact/DecisionLog.

## Supplier Check flow
1. Принимает shortlist.
2. Делает supplier-oriented search.
3. Извлекает supplier data.
4. Считает базовую unit economics.
5. Применяет quality gates.
6. Возвращает `passed | quick_check | failed`.
7. Сохраняет trace и artifacts.

## Ограничения v1
- Нет browser automation.
- Нет массового scraping framework.
- Нет асинхронных очередей.
- Real adapters минимальные и intentionally constrained.
