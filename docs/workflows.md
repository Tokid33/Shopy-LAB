# Workflows

## 1) Product Stage
1. Создать `ProductHypothesis`.
2. Заполнить `ProductCard`.
3. Выполнить scoring.
4. Сохранить `Decision(stage=product)`.
5. При shortlist: добавить `SupplierAssessment`, `CompetitorSnapshot`, `UnitEconomics`.

## 2) Site Stage
1. Создать `Offer`.
2. Создать `LandingPage` с блоками hero/benefits/proof/offer/faq.
3. Зафиксировать `Decision(stage=site)` при необходимости.

## 3) Traffic Stage
1. Создать `TrafficTest`.
2. Добавить 3+ `Creative`.
3. Добавить `MetricSnapshot`.
4. Принять `Decision(stage=traffic)`.
5. Зафиксировать `FinalDecision` и обязательный `Postmortem`.
6. Сохранить `ArtifactPackage` и `KnowledgeBase`.

## Demo workflow
Реализован в `app/services/workflow.py` и доступен через:
- CLI: `python -m app.cli.demo_cycle`
- API: `POST /demo-cycle`

## Export workflow (cycle report)
После завершения или в любой момент цикла можно выгрузить единый отчёт:
- CLI: `python -m app.cli.export_cycle_report --hypothesis-id <id>`
- Форматы: JSON + Markdown
- Если часть данных отсутствует, секция маркируется как `missing` без падения процесса.

## Agent workflows (demo)
1. `POST /agents/product-scout/run` — запускает Product Scout Agent в mock-режиме.
2. `POST /agents/supplier-check/run` — запускает Supplier Check Agent в mock-режиме.
3. `GET /agents/runs/{run_id}` — возвращает статус и сохранённый output запуска.

## Agent workflows (real)
1. `POST /agents/product-scout/run-real` — ограниченный real execution path через adapters.
2. `POST /agents/supplier-check/run-real` — ограниченный real execution path через adapters.
3. `GET /agents/providers/health` — health/config visibility по провайдерам.

## Operator path v1.0
1. Поднять БД (`alembic upgrade head`)
2. Поднять API
3. Выполнить `POST /demo-cycle`
4. Экспортировать report (`python -m app.cli.export_cycle_report --hypothesis-id 1`)
5. Проверить `GET /agents/providers/health`
6. Запустить mock agent runs
7. При валидной env-конфигурации запустить real agent runs
