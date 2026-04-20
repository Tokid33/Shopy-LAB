# Architectural / Product Decisions (MVP)

## D-001: SQLite + SQLAlchemy + Alembic
Принято для быстрого локального старта и прозрачных миграций.

## D-002: Rule-based scoring
Используется линейная взвешенная формула (без ML) для объяснимости решений.

## D-003: One-cycle orchestration в service layer
Выбран service workflow как самый быстрый и устойчивый MVP-вариант, плюс CLI/API триггеры.

## D-004: Источник истины при конфликте артефактов
В репозитории присутствуют BPMN/UML/ER изображения, но без текстовой спецификации. Для MVP источником истины считается текущая доменная модель в `app/models/entities.py`, а расхождения фиксируются здесь.

## D-005: Unit economics как отдельный слой v0.2
Юнит-экономика выделена в отдельную сущность `UnitEconomics` и сервис расчёта для повторного использования и аналитичности.

## D-006: Строгая финализация v0.2
Финал цикла фиксируется через `FinalDecision` + `Postmortem` с ограничением one-per-hypothesis и проверкой согласованности `final_outcome == next_action`.

## D-007: Cycle report export как единый артефакт цикла
Добавлен service-layer экспорт отчёта цикла в JSON + Markdown из одной точки сборки данных.
Правило: при неполных данных не падать, а явно маркировать секции как `missing`.

## D-008: Agent-ready foundation через mock adapters
Добавлен минимальный agent слой (run/task/artifact/decision-log) и интерфейсы провайдеров.
Реальные интеграции отложены; демо-режим работает на fake adapters для безопасного локального старта.

## D-009: Dual-mode agent execution (mock + real)
Mock mode остаётся default и безопасным.
Real mode включается конфигом и проходит через provider factory с controlled failures при misconfiguration.
