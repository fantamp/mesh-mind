# Технические Требования: Реализация Мультиагентной Системы

> Для ИИ-разработчиков и людей-разработчиков. Перед началом ОБЯЗАТЕЛЬНО изучите указанные ссылки.

---

## Обязательное Изучение Документации

### Перед началом работы изучите:

**1. Google Agent Development Kit (ADK)**
> [!IMPORTANT]
> **CRITICAL**: Before writing any code using ADK, you MUST read the [Official Documentation](https://google.github.io/adk-docs/).
> Common mistake: Trying to call `agent.run()` directly. You MUST use `Runner` or helper functions like `run_agent_sync`.

- [Официальная документация](https://google.github.io/adk-docs/)
- [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [Custom Function Tools](https://google.github.io/adk-docs/tools-custom/function-tools/)
- [Sessions & Memory](https://google.github.io/adk-docs/sessions/)
- [Evaluation](https://google.github.io/adk-docs/evaluation/)
- [Примеры на GitHub](https://github.com/google/adk-python/tree/main/examples)

**2. Документация проекта**
- [Продуктовые Требования](./multi-agent-system.md) — логика агентов
- [Архитектура Агентов](../architecture/multi-agent-design.md) — схемы взаимодействия
- [Правила Разработки](../../.agent/rules/) — code style, testing

---

## Архитектурные Паттерны

### 1. Sub-Agents Pattern (для Orchestrator)

**Когда использовать**: Когда главный агент должен **полностью делегировать** задачу.

**Как работает**:
- Orchestrator использует `sub_agents=[]` параметр
- LLM **автоматически** определяет к какому sub-agent передать управление
- Контекст передается через shared session state

**Преимущества**:
- LLM-driven delegation (не нужна явная логика роутинга)
- Идеально для Coordinator/Dispatcher pattern

**Референс**: [Coordinator Pattern](https://google.github.io/adk-docs/agents/multi-agents/#coordinatordispatcher-pattern)

### 2. AgentTool Pattern (для Simple Summarizer)

**Когда использовать**: Когда нужно **инкапсулировать** конкретную задачу.

**Как работает**:
- Агент оборачивается в `AgentTool(agent=...)`
- Работает в **изолированном контексте** (temporary context)
- Четкий input/output контракт

**Преимущества**:
- Переиспользуемость
- Инкапсуляция
- Простота

**Референс**: [Agent Hierarchy](https://google.github.io/adk-docs/agents/multi-agents/#agent-hierarchy-parent-agent-sub-agents)

---

## Структура Файлов Агентов

```
ai_core/agents/
├── orchestrator/
│   └── agent.py            # Главный координатор
├── chat_summarizer/
│   └── agent.py            # Суммаризация чата
├── summarizer/
│   └── agent.py            # Простой суммаризатор (Tool)
└── chat_observer/
    └── agent.py            # Наблюдатель (Search + QA)
```

**Каждый agent.py содержит**:
- Создание агента через `LlmAgent` из ADK
- `InMemorySessionService` для сессий
- `Runner` для выполнения
- Экспорт через `agent` и `runner`

**Референс**: [LLM Agents Guide](https://google.github.io/adk-docs/agents/llm-agents/)

---

## Детали Реализации Агентов

### Агент-Оркестратор

**Ключевые моменты**:
- **Model**: `gemini-2.5-flash`
- **Sub-Agents**: Chat Summarizer, Chat Observer
- **Session**: `chat_id` = `session_id`
- **Natural Language**: понимает запросы как без команд, так и с командами /ask или /summary
- **Instruction**: описывает логику роутинга

**Референс**: [Coordinator Pattern](https://google.github.io/adk-docs/agents/multi-agents/#coordinatordispatcher-pattern)

### Агент-Суммаризатор Чата

**Ключевые моменты**:
- Использует `fetch_messages` tool (получение из SQLite)
- Использует Simple Summarizer как `AgentTool`
- Возвращает саммари в Telegram

### Обработка пересланных сообщений (Forwarded Messages)

**Логика**:
- Если сообщение переслано (is_forwarded = True):
    - **Только сохраняется** в базу данных.
    - **НЕ отправляется** в Оркестратор.
    - Бот молчит (или отвечает "Saved" если не silent mode).
- В Оркестратор попадают только прямые сообщения от пользователя.

### Простой Суммаризатор

**Функциональность**:
- Генерирует саммари текста
- Используется Chat Summarizer через `AgentTool`
- Нет собственных tools (только LLM)

### Агент-Наблюдатель (Chat Observer)

**Ключевые моменты**:
- Использует `fetch_messages` tool
- Поиск по автору, дате, ключевым словам
- Отвечает на вопросы по истории чата (QA)
- Фильтрует по `chat_id`

---

## Управление Сессиями

**Принцип**: `chat_id` = `session_id`

**InMemorySessionService**:
```python
from google.genai.types import InMemorySessionService

session_service = InMemorySessionService()
```

**Почему InMemory?**
- Для MVP достаточно
- Контекст теряется при перезапуске (не критично)
- Можно заменить на persistent позже

**Референс**: [Sessions Guide](https://google.github.io/adk-docs/sessions/)

---

## Tools (Инструменты)

### 1. fetch_messages

**Назначение**: Получение сообщений из SQLite БД

**Параметры**:
- `chat_id: str` — ID чата (обязательно, для изоляции)
- `limit: int` — количество сообщений
- `since: datetime | str` (опционально) — с какой даты/времени
- `author_id: str` (опционально) — фильтр по id пользователя
- `author_nick: str` (опционально) — фильтр по никнейму (username без @)
- `contains: str` (опционально) — подстрока для поиска по тексту

**Возвращает**: Читаемый текстовый список вида `[YYYY-MM-DD HH:MM:SS] Имя Фамилия (@username): сообщение` или `"No messages found."`

**Референс**: Смотри `ai_core/tools/messages.py`

---

## Тестирование Агентов

### 1. Ручное Тестирование: `adk web`

Запуск Web UI для интерактивного тестирования:

```bash
make adk-web
```

Откроется `http://localhost:8000`

**Что проверять**:
- Правильность роутинга Orchestrator'а
- Корректность tool calls
- Качество ответов агентов

### 2. Автоматическое Тестирование: `adk eval`

**Структура eval тестов**:
```
tests/agents/eval/
├── orchestrator/
│   └── routing_eval.yaml
└── summarizer/
    └── quality_eval.yaml
```

**Запуск**:
```bash
adk eval tests/agents/eval/
```

**Критерии оценки**:
- `tool_trajectory_correctness` — правильность tool calls
- `response_quality_rubric` — качество ответа
- `final_response_match` — совпадение с ожидаемым

**Референс**: [Evaluation Guide](https://google.github.io/adk-docs/evaluation/)

### 3. Unit Тесты: pytest

**Что тестировать**:
- Отдельные функции tools
- Интеграцию между компонентами
- Изоляцию по chat_id

```bash
pytest tests/ -v
```

---

## Definition of Done

**Агент считается готовым**, если:

**Код**:
- ✅ Следует паттернам (Sub-Agents или AgentTool)
- ✅ Использует ADK правильно
- ✅ Есть type hints
- ✅ Комментарии на русском

**Тестирование**:
- ✅ Ручное тестирование через `adk web` пройдено
- ✅ Созданы eval тесты (score > 0.7)
- ✅ Unit тесты проходят

**Документация**:
- ✅ Instruction агента ясна и точна
- ✅ Tools описаны в docstrings
- ✅ Создан walkthrough.md с proof of work

**Изоляция**:
- ✅ Все tools фильтруют по `chat_id`
- ✅ Нет утечки данных между чатами
- ✅ Тесты подтверждают изоляцию

---

## Полезные Ссылки

**Документация**:
- [Продуктовые Требования](./multi-agent-system.md)
- [Архитектура Агентов](../architecture/multi-agent-design.md)
- [Правила Тестирования](../../.agent/rules/05-testing.md)

**Google ADK**:
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [Evaluation](https://google.github.io/adk-docs/evaluation/)
- [Examples on GitHub](https://github.com/google/adk-python/tree/main/examples)
