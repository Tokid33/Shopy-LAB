# Жёсткий аудит Shopify Lab MVP v0.1

## 1) Какие сущности реально участвовали в demo-cycle v0.1
### Участвовали
- `ProductHypothesis`, `ProductCard`
- `SupplierAssessment`, `CompetitorSnapshot`
- `Offer`, `LandingPage`
- `TrafficTest`, `Creative`, `MetricSnapshot`
- `Decision`, `ArtifactPackage`, `KnowledgeBase`

### Не участвовали как отдельный строгий слой
- `UnitEconomics` (отсутствовала как сущность)
- Финальная фиксация решения и postmortem были нестрогими и смешаны с обычной `Decision`.

## 2) Слабые места happy-path workflow v0.1
1. Unit economics считалась неявно и не сохранялась нормализованно.
2. Финальное решение (`kill/iterate/scale`) не имело строгой one-per-hypothesis фиксации.
3. Postmortem не был обязательным структурированным артефактом.
4. Нельзя было валидировать согласованность final decision и next action postmortem.

## 3) Где модель была неполна / нестрога
- Отсутствовала отдельная сущность `UnitEconomics`.
- Не было `FinalDecision` и `Postmortem` с ограничением уникальности на гипотезу.
- Не было explicit сервиса доменной финализации цикла.

## 4) Edge-cases, не покрытые v0.1
- Повторная запись финального решения для одной гипотезы.
- Несогласованность final decision vs postmortem next_action.
- Негативный/нулевой ad cost и искажение break-even расчёта.

## 5) Минимальный v0.2 scope (без распыления)
1. Ввести `UnitEconomics` как отдельную сущность + сервис расчёта.
2. Ввести строгую финализацию через `FinalDecision` + `Postmortem`.
3. Добавить минимальные тесты на эти две зоны.

> Всё остальное (UI, интеграции, сложный orchestration) отложить.
