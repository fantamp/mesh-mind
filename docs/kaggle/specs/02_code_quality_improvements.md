# Спека: Улучшение качества кода и документации

## Цель
Улучшить Technical Implementation score (50 баллов) через:
1. Добавление Design Decision комментариев в агентах
2. Удаление dead code
3. Демонстрацию Session Management паттернов

## Задачи

### 1. Design Decision комментарии в агентах

**Файлы для обновления:**
- `ai_core/agents/orchestrator/agent.py`
- `ai_core/agents/chat_summarizer/agent.py`
- `ai_core/agents/chat_observer/agent.py`

**Что добавить:**
Блок комментариев **перед** определением `agent = LlmAgent(...)`, объясняющий архитектурные решения.

**Пример для orchestrator/agent.py:**
```python
# ============================================================================
# DESIGN DECISIONS: Orchestrator Agent
# ============================================================================
# 
# 1. Multi-agent approach via sub_agents:
#    - Allows LLM-driven delegation based on natural language intent
#    - Avoids brittle keyword matching (e.g., if/else on specific words)
#    - Orchestrator analyzes user query and routes to specialized agent
#
# 2. Silent mode (return "null" for casual messages):
#    - Prevents bot spam in group chats
#    - Only responds to direct questions/commands
#
# 3. Session reuse (session_id = chat_id):
#    - InMemorySessionService preserves conversation context per chat
#    - Enables multi-turn interactions without losing history
# ============================================================================
```

Для других агентов добавить аналогичные комментарии про их специфику (tools, sub-agents, etc).

---

### 2. Удалить dead code из `ai_core/storage/db.py`

**Удалить следующие элементы:**
- Класс `ChatState` (не используется)
- Класс `DocumentMetadata` (не используется)
- Функцию `get_messages_after_id()` (не вызывается)
- Функцию `update_chat_state()` (не вызывается)
- Функцию `save_document_metadata()` (не вызывается)
- Функцию `get_chat_state()` (не вызывается)

**Оставить только:**
- Класс `Message` (используется агентами)
- Функции: `init_db()`, `save_message()`, `get_messages()`

---

### 3. Session Management комментарии

**Файл:** `ai_core/common/adk.py`

Добавить блок комментариев в начале файла (после imports), объясняющий session management strategy:

```python
# ============================================================================
# SESSION MANAGEMENT DESIGN
# ============================================================================
# 
# Strategy: Different session patterns for different agents
# 
# 1. Orchestrator (stateful):
#    - session_id = chat_id (e.g., "123456789")
#    - Preserves conversation context across multiple user messages
#    - Enables follow-up questions and context awareness
# 
# 2. Summarizer (stateless):
#    - session_id = unique UUID (e.g., "summarizer_chat123_uuid")
#    - No context needed - each summarization is independent
#    - Fresh session per request
# 
# InMemorySessionService handles both patterns seamlessly.
# ============================================================================
```

**Файл:** `docs/architecture/multi-agent-design.md`

Добавить новую секцию перед "## Технические Детали":

```markdown
## Session Management Strategy

**InMemorySessionService** используется для управления сессиями агентов.

### Паттерны использования:

| Агент | session_id | Тип | Зачем |
|-------|-----------|------|-------|
| Orchestrator | `chat_id` | Stateful | Сохраняет контекст диалога |
| Chat Summarizer | `unique UUID` | Stateless | Каждая суммаризация независима |
| Chat Observer | наследует от Orchestrator | Stateful | Использует контекст из Orchestrator |

**Преимущества подхода:**
- Гибкость: разные агенты используют разные стратегии
- Простота: InMemorySessionService прозрачно управляет обоими паттернами
```

---

### 4. Обновить README.md

**Изменения:**

1. Удалить упоминания несуществующих компонентов:
   - Удалить строки про Web UI, CLI (если есть)

2. Добавить секцию "Key ADK Concepts Demonstrated" после "## Features":

```markdown
## Key ADK Concepts Demonstrated

✅ **Multi-agent System**: Orchestrator coordinates specialized sub-agents  
✅ **Custom Tools**: `fetch_messages` with advanced filtering  
✅ **Sessions & Memory**: InMemorySessionService with stateful/stateless patterns  
✅ **Agent Evaluation**: ADK eval framework with comprehensive test coverage  
✅ **Observability**: Structured logging via loguru  
```

## Definition of Done

- [ ] Design Decision комментарии добавлены во все три agent.py файла
- [ ] Dead code удалён из `ai_core/storage/db.py`
- [ ] Session Management комментарии добавлены в `ai_core/common/adk.py`
- [ ] Секция "Session Management Strategy" добавлена в `docs/architecture/multi-agent-design.md`
- [ ] README.md обновлён (удалены несуществующие компоненты, добавлена секция ADK Concepts)
- [ ] `make test` проходит успешно
