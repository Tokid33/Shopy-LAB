# Workflows

## 1) Product Stage
1. Создать `ProductHypothesis`.
2. Заполнить `ProductCard`.
3. Выполнить scoring.
4. Сохранить `Decision(stage=product)`.
5. При shortlist: добавить `SupplierAssessment`, `CompetitorSnapshot`, расчёт экономики.

## 2) Site Stage
1. Создать `Offer`.
2. Создать `LandingPage` с блоками hero/benefits/proof/offer/faq.
3. Зафиксировать `Decision(stage=site)` при необходимости.

## 3) Traffic Stage
1. Создать `TrafficTest`.
2. Добавить 3+ `Creative`.
3. Добавить `MetricSnapshot`.
4. Принять `Decision(stage=traffic)`.
5. Сохранить `ArtifactPackage` и `KnowledgeBase`.

## Demo workflow
Реализован в `app/services/workflow.py` и доступен через:
- CLI: `python -m app.cli.demo_cycle`
- API: `POST /demo-cycle`
