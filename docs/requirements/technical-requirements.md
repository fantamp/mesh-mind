# Технические Требования: Реализация Мультиагентной Системы

> Для ИИ-разработчиков и людей-разработчиков. Перед началом ОБЯЗАТЕЛЬНО изучите указанные ссылки.

---

## Обязательное Изучение Документации

### Перед началом работы изучите:

**1. Google Agent Development Kit (ADK)**
- [Официальная документация](https://google.github.io/adk-docs/)
- [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [Custom Function Tools](https://google.github.io/adk-docs/tools-custom/function-tools/)
- [Sessions & Memory](https://google.github.io/adk-docs/sessions/)
- [Evaluation](https://google.github.io/adk-docs/evaluation/)
- [Примеры на GitHub](https://github.com/google/adk-python/tree/main/examples)

**2. Документация проекта**
- [Продуктовые Требования](./multi-agent-system.md) — логика агентов
- [Архитектура Агентов](../architecture/multi-agent-design.md) — схемы взаимодействия
- [Правила Разработки](../../agent_template/rules/) — code style, testing

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
- Идеально для Coordinator/Dispatcher pattern Специализированные агенты ведут сложные диалоги

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
│   └── agent.py            # Простой суммаризатор
├── qa/
│   └── agent.py            # QA Agent
└── chat_observer/
    └── agent.py            # Наблюдатель
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
- **Sub-Agents**: Chat Summarizer, QA Agent, Chat Observer
- **Session**: `chat_id` = `session_id`
- **Natural Language**: понимает запросы как без команд, так и скомандами /ask или /summary
- **Instruction**: описывает логику роутинга

**Референс**: [Coordinator Pattern](https://google.github.io/adk-docs/agents/multi-agents/#coordinatordispatcher-pattern)

### Агент-Суммаризатор Чата

**Ключевые моменты**:
- Использует `fetch_messages` tool (получение из SQLite)
- Использует Simple Summarizer как `AgentTool`
- Возвращает саммари в Telegram (НЕ сохраняет в VectorDB)

### Простой Суммаризатор

**Функциональность**:
- Генерирует саммари текста
- Используется Chat Summarizer через `AgentTool`
- Нет собственных tools (только LLM)

### Агент-Отвечатель (QA Agent)

**Ключевые моменты**:
- Использует `search_knowledge_base` tool (поиск в VectorDB)
- Фильтрует по `chat_id` в метаданных
- **Честно отвечает "я не знаю"** при отсутствии информации
- Указывает источники

**Критически важно**: Instruction должна явно требовать "скажи 'я не знаю'" если нет ответа.

### Агент-Наблюдатель (Chat Observer)

**Ключевые моменты**:
- Использует `fetch_messages` tool
- Поиск по автору, дате, ключевым словам
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
- `chat_id: str` — ID чата (обязательно)
- `limit: int` — количество сообщений
- `since: datetime` (опционально) — с какой даты
- `author: str` (опционально) — автор сообщений

**Возвращает**: `List[Message]`

**Референс**: Смотри `ai_core/storage/db.get_messages()`

### 2. search_knowledge_base

**Назначение**: Поиск в векторной БД (ChromaDB)

**Параметры**:
- `query: str` — поисковый запрос
- `chat_id: str` — ID чата (для фильтрации)
- `top_k: int` — количество результатов (по умолчанию 5)

**Возвращает**: `List[Dict]` с полями `content`, `metadata`, `score`

**Критически важно**: ВСЕГДА фильтровать по `chat_id` в метаданных!

**Референс**: Смотри `ai_core/rag/knowledge_base.py`

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
├── qa/
│   ├── known_answers_eval.yaml
│   └── unknown_answers_eval.yaml
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
- [Правила Тестирования](../../agent_template/rules/04-testing.md)

**Google ADK**:
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [Evaluation](https://google.github.io/adk-docs/evaluation/)
- [Examples on GitHub](https://github.com/google/adk-python/tree/main/examples)
