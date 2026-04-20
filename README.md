# Shopify Lab MVP

Минимальный, но рабочий контур системы проверки e-commerce гипотез по циклу:

**ТОВАР → САЙТ → ТРАФИК → РЕШЕНИЕ**

## Что уже было в репозитории
- Набор BPMN/UML/ER диаграмм в виде изображений (`*.png`), отражающих процессы и архитектурный контекст.
- Пустой `README.md`.

## Что сделано в MVP
- Реализован Python-проект на FastAPI + SQLAlchemy + Pydantic + Alembic + SQLite.
- Добавлена доменная модель с 12 ключевыми сущностями.
- Добавлена доменная модель с расширением v0.2: `UnitEconomics`, `FinalDecision`, `Postmortem`.
- Добавлен rule-based scoring engine для этапа товара.
- Добавлен service workflow одного полного demo-цикла.
- Добавлена строгая финализация цикла: отдельные сущности final decision и postmortem.
- Добавлен единый export cycle report (JSON + Markdown) по `hypothesis_id`.
- Добавлены тесты: scoring, smoke workflow, model checks.
- Добавлена документация по архитектуре, доменной модели, workflow и решениям.

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
