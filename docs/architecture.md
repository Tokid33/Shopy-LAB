# Архитектура MVP Shopify Lab

## Цель
Локальный доменный контур для цикла **ТОВАР → САЙТ → ТРАФИК → РЕШЕНИЕ** с хранением артефактов и выводов.

## Слои
- **API (FastAPI)**: health + запуск demo cycle.
- **Service layer**: scoring и orchestration одного цикла.
- **Repository layer**: базовые операции с гипотезами.
- **Data layer**: SQLAlchemy модели + Alembic миграции + SQLite.
- **Tests**: unit/smoke/model проверки.

## Принципы MVP
1. Ясные имена и простая трассировка решений.
2. Rule-based scoring без ML.
3. Минимум инфраструктуры: один процесс + SQLite.
4. Сразу заложены сущности для дальнейшей автоматизации.
