# Спеки Упрощения Проекта Mesh Mind

Данная папка содержит спецификации для упрощения проекта.

## Список спек

1. **[01_telegram_handlers_simplification.md](01_telegram_handlers_simplification.md)** - Упрощение Telegram handlers
   - Удаление команд `/summary` и `/ask`
   - Удаление автоматической суммаризации форвардов
   - Удаление VectorDB (ChromaDB)
   - Объединение qa агента в chat_observer

2. **[02_remove_webui_and_cli.md](02_remove_webui_and_cli.md)** - Удаление Web UI и CLI
   - Удаление Streamlit UI
   - Удаление CLI инструментов
   - Обновление зависимостей

3. **[03_remove_api.md](03_remove_api.md)** - Удаление API
   - Удаление FastAPI слоя
   - Прямая интеграция Telegram Bot с AI Core
   - Обновление архитектуры

4. **[04_update_rules.md](04_update_rules.md)** - Обновление правил
   - Обновление `.agent/rules/01-project-overview.md`
   - Обновление `.agent/rules/02-architecture.md`
   - Финальная архитектура проекта

5. **[05_cleanup_and_verification.md](05_cleanup_and_verification.md)** - Очистка и верификация
   - Очистка зависимостей (requirements.txt)
   - Ревизия .gitignore
   - Финальная верификация работоспособности

## Порядок выполнения

Спеки должны выполняться **последовательно** в указанном порядке:
1. Сначала Спека 01
2. Затем Спека 02
3. Затем Спека 03
4. Затем Спека 04
5. В конце Спека 05

## Цель

Упростить проект, оставив только:
- Telegram Bot (основной интерфейс)
- AI Core с агентами (Orchestrator, Chat Summarizer, Chat Observer)
- SQLite (единственное хранилище данных)
