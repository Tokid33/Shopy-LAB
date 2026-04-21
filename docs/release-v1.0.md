# Shopify Lab v1.0 Release

## Что входит в v1.0
- Стабильное локальное backend-ядро цикла Product→Site→Traffic→Decision
- SQLAlchemy domain model + Alembic migrations
- Rule-based scoring
- Unit economics
- Strict finalization (`FinalDecision` + `Postmortem`)
- Cycle report export (JSON + Markdown)
- Agent runtime layer (mock + constrained real)
- Provider health endpoint
- Prompt loading + traceability
- State machine + domain invariants
- Тесты на критические сценарии

## Что НЕ входит
- UI
- Auth
- Shopify API
- Telegram/n8n/Google Sheets
- Celery/Redis/Kafka
- Browser automation

## Проверенные сценарии
1. install deps
2. alembic upgrade
3. demo-cycle
4. cycle report export
5. mock agent runs
6. provider health check
7. controlled failure при real misconfiguration
8. state machine valid/invalid transitions

## Локальный запуск
```bash
python -m pip install -e .[dev]
python -m alembic upgrade head
uvicorn app.main:app --reload
python -m app.cli.demo_cycle
python -m app.cli.export_cycle_report --hypothesis-id 1
pytest -q
```

## Ограничения
- Real mode зависит от внешних API и env конфигурации
- HTTP fetch adapter intentionally simple (no browser)
- LLM extraction — минимальный structured path

## Следующий шаг после v1.0
- добавить sinks (например sheets/warehouse) без ломки state discipline
- добавить batching/scheduling для agent runs
- расширить наблюдаемость (metrics + audit trails)
