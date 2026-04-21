# Agent Architecture (usable execution layer v1)

## Что переиспользовано
- Существующий MVP и domain core.
- Existing scoring engine.
- Existing unit-economics service.
- Existing AgentRun/Task/Artifact/DecisionLog foundation.

## Новые ключевые элементы
1. **Execution configuration layer**
   - централизован в `app/core/config.py`
2. **Provider factory / resolution**
   - `get_search_provider()`
   - `get_fetch_provider()`
   - `get_llm_extractor()`
3. **Prompt registry/loading**
   - runtime загрузка prompt templates
   - trace: path + version
4. **Real execution path**
   - Brave/SerpAPI search (минимально)
   - HTTP fetch adapter
   - OpenAI-compatible extractor
5. **Traceability**
   - trace_id
   - provider_snapshot
   - prompt_path/prompt_version
   - warnings/raw artifacts

## Quality gates
### Product Scout invalid if
- `product_name` пустой
- `signal` не в `green|yellow|red`
- score невозможно вычислить

### Supplier Check invalid if
- `supplier_name` пустой
- `unit_cost/ship_cost` невалидны
- supplier status вне `passed|quick_check|failed`

## Controlled failure policy
- Real mode misconfigured → controlled API error (400)
- Invalid extracted output → run failed + raw artifact
- Ошибки провайдеров не валят весь сервис глобально
