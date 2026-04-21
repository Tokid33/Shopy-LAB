# Shopify Lab v1.0.0

Минимальный, но рабочий контур системы проверки e-commerce гипотез по циклу:

**ТОВАР → САЙТ → ТРАФИК → РЕШЕНИЕ**

## Что уже было в репозитории
- Набор BPMN/UML/ER диаграмм в виде изображений (`*.png`), отражающих процессы и архитектурный контекст.
- Пустой `README.md`.

## Что входит в v1.0
- Реализован Python-проект на FastAPI + SQLAlchemy + Pydantic + Alembic + SQLite.
- Добавлена доменная модель с 12 ключевыми сущностями.
- Добавлена доменная модель с расширением v0.2: `UnitEconomics`, `FinalDecision`, `Postmortem`.
- Добавлен rule-based scoring engine для этапа товара.
- Добавлен service workflow одного полного demo-цикла.
- Добавлена строгая финализация цикла: отдельные сущности final decision и postmortem.
- Добавлен единый export cycle report (JSON + Markdown) по `hypothesis_id`.
- Добавлен первый agent-ready слой: Product Scout Agent и Supplier Check Agent (demo/mock).
- Добавлены тесты: scoring, smoke workflow, model checks.
- Добавлена документация по архитектуре, доменной модели, workflow и решениям.
- Добавлена state machine дисциплина и release docs v1.0.

## Структура
- `app/main.py` — FastAPI app
- `app/models/` — SQLAlchemy сущности
- `app/schemas/` — Pydantic схемы
- `app/services/` — scoring + workflow
- `app/repositories/` — базовый репозиторий гипотез
- `app/db/` — база и сессия
- `migrations/` — Alembic
- `docs/` — архитектурные документы
- `tests/` — тесты

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## База данных и миграции
```bash
alembic upgrade head
```

SQLite-файл будет создан как `shopify_lab.db`.

## Запуск API
```bash
uvicorn app.main:app --reload
```

Endpoints:
- `GET /health`
- `POST /demo-cycle`
- `POST /agents/product-scout/run`
- `POST /agents/supplier-check/run`
- `POST /agents/product-scout/run-real`
- `POST /agents/supplier-check/run-real`
- `GET /agents/runs/{run_id}`
- `GET /agents/providers/health`

## Запуск demo-cycle через CLI
```bash
python -m app.cli.demo_cycle
```

## Экспорт cycle report через CLI
```bash
python -m app.cli.export_cycle_report --hypothesis-id 1
```

По умолчанию отчёты сохраняются в `artifacts/reports/` в двух форматах:
- `cycle_report_<id>.json`
- `cycle_report_<id>.md`

Если часть данных цикла отсутствует, это явно помечается как `missing` в отчёте.

## Запуск demo-агентов
Пример Product Scout:
```bash
curl -X POST http://localhost:8000/agents/product-scout/run \
  -H "Content-Type: application/json" \
  -d '{"market":"US","categories":["kitchen","wellness"],"limit":3}'
```

Пример Supplier Check:
```bash
curl -X POST http://localhost:8000/agents/supplier-check/run \
  -H "Content-Type: application/json" \
  -d '{"shortlist_items":[{"product_name":"Demo Product","target_price":39,"cost_of_goods":11,"shipping_cost":4}]}'
```

## Agent execution configuration
По умолчанию проект работает в безопасном `mock` режиме.

Пример env для real path:
```bash
export AGENT_MODE=real
export SEARCH_PROVIDER=brave
export FETCH_PROVIDER=http
export LLM_PROVIDER=openai_compatible
export SEARCH_API_KEY=your_search_key
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=your_llm_key
export LLM_MODEL=gpt-4o-mini
```

Дополнительно поддерживаются:
- `REQUEST_TIMEOUT_SECONDS`
- `MAX_SEARCH_RESULTS`
- `MAX_FETCH_PAGES`
- `MAX_PAGE_TEXT_CHARS`
- `ENABLE_PROMPT_TRACING`
- `ENABLE_RAW_ARTIFACT_CAPTURE`

Проверка готовности провайдеров:
```bash
curl http://localhost:8000/agents/providers/health
```

Запуск real endpoints:
```bash
curl -X POST http://localhost:8000/agents/product-scout/run-real \
  -H "Content-Type: application/json" \
  -d '{"market":"US","categories":["kitchen"],"limit":3}'
```

## Operator path (v1.0)
```bash
python -m pip install -e .[dev]
python -m alembic upgrade head
uvicorn app.main:app --reload
python -m app.cli.demo_cycle
python -m app.cli.export_cycle_report --hypothesis-id 1
pytest -q
```

## Тесты
```bash
pytest
```

## Rule-based scoring (этап товара)
Поля:
- `problem_or_desire_score` (вес 0.30)
- `visual_potential_score` (вес 0.20)
- `margin_score` (вес 0.25)
- `ad_risk_score` (вес 0.15)
- `logistics_risk_score` (вес 0.10)

Формула:
`total_score = (Σ score_i * weight_i) * 10`

Пороговые решения:
- `shortlist` при `>= 75`
- `reserve` при `55..74.99`
- `reject` при `< 55`

## Следующий шаг (после MVP)
1. CRUD API по ключевым сущностям.
2. Экспорт артефактов и отчётов postmortem.
3. Автоматизация повторного запуска циклов по шаблонам.

## v0.2 audit
Подробный аудит текущего MVP и минимальный scope v0.2: `docs/audit-v0.1.md`.

## v0.2 hard audit
Подробный аудит текущего состояния v0.2 и rationale по cycle report export: `docs/audit-v0.2.md`.

## Release docs
- `docs/state-machine.md`
- `docs/release-v1.0.md`
- `CHANGELOG.md`
