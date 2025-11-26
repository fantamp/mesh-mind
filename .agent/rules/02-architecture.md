# Архитектурные Принципы

## Общая Архитектура

Проект следует принципу разделения на независимые компоненты:

- **Telegram Bot** (`telegram_bot/`) — отдельное приложение, работает через Long Polling
- **AI Core** (`ai_core/`) — центральный сервис с агентами, API, UI
- **CLI** (`cli/`) — инструменты для административных задач

### Границы Компонентов

**Важно**: Следи за тем, чтобы не нарушались границы между компонентами. Если для решения задачи требуется изменить архитектуру — сообщи об этом.

## Структура Проекта

Детальная структура каталогов описана в docs/architecture/project-structure.md.

Краткая структура:

```
ai_core/          # Основной сервис
  agents/         # AI-агенты (Google ADK)
  api/            # FastAPI эндпоинты
  ui/             # Streamlit интерфейс
  rag/            # Работа с векторной БД
  common/         # Общие утилиты
  
telegram_bot/     # Telegram бот
cli/              # CLI инструменты
tests/            # Тесты
data/             # Локальное хранилище (в .gitignore)
```

## Паттерны Агентов

### Coordinator/Dispatcher Pattern

**Orchestrator** = Supervisor, специализированные агенты = Workers. Централизованный контроль потока.

### Sub-Agents Pattern

Используется для делегирования задач. Orchestrator использует `sub_agents=[]`, LLM автоматически определяет к какому агенту передать управление.

**Референс**: [ADK Coordinator Pattern](https://google.github.io/adk-docs/agents/multi-agents/#coordinatordispatcher-pattern)

### AgentTool Pattern

Используется для инкапсуляции конкретных задач. Агент оборачивается в `AgentTool(agent=...)` и работает в изолированном контексте.

**Референс**: [ADK Agent Hierarchy](https://google.github.io/adk-docs/agents/multi-agents/#agent-hierarchy-parent-agent-sub-agents)

## Хранение Данных

- **SQLite** (`data/db/`) — сырые сообщения, метаданные
- **ChromaDB** (`data/vector_store/`) — векторные представления для поиска
- **File System** (`data/media/`) — медиа файлы

### Изоляция по chat_id

**Критически важно**: каждый документ в VectorDB содержит `chat_id` в метаданных. Все tools фильтруют по `chat_id`. Агенты видят только данные своего чата.

## Ключевые Библиотеки

- **НЕ использовать** `google.generativeai` напрямую
- **Использовать** Google Agent Development Kit (ADK) для создания агентов
- Документация: https://google.github.io/adk-docs/

## Детальная Архитектура

> Пути относительно корня проекта

Полное описание архитектуры системы и агентов в документации:

- docs/architecture/system-overview.md
- docs/architecture/multi-agent-design.md
