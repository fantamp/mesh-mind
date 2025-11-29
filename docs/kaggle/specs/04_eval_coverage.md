# Спека: Comprehensive ADK Eval Coverage

## Цель
Создать eval test cases для всех агентов, демонстрируя качество и надежность системы.

**Impact:** Technical Implementation (50 баллов) - "Agent evaluation" обязательный ADK концепт.

## Предварительная задача

**ВАЖНО:** Перед реализацией необходимо изучить:

1. **Официальная документация ADK Eval:**
   - https://google.github.io/adk-docs/evaluation/
   - Особенно разделы про eval set format и best practices

2. **Существующий пример:**
   - Изучить `tests/agents/eval/chat_observer/fetch_messages_eval.evalset.json`
   - Понять структуру: eval_id, conversation, intermediate_data, tool_uses

3. **Best Practices для MVP:**
   - Это MVP → цель: **демонстрация** возможности eval, а не 100% coverage
   - 3-4 кейса на агента достаточно
   - Фокус на happy path + 1-2 edge case

## Задача

Создать eval test cases для агентов, у которых их ещё нет:
- **Orchestrator** (создать новые)
- **Chat Summarizer** (создать новые)
- **Chat Observer** (уже есть — не трогать)

### 1. Orchestrator Eval Test Cases

**Папка:** `tests/agents/eval/orchestrator/`

**Файлы:**
- `routing_eval.evalset.json` — тесты роутинга
- `test_config.json` — конфигурация для adk eval

**Кейсы (3-4 штуки):**

1. **happy_routing_to_summarizer** — запрос на summary → должен вызвать chat_summarizer
2. **happy_routing_to_observer** — запрос с вопросом → должен вызвать chat_observer
3. **silent_mode_casual_message** — casual сообщение → "null" или пустой ответ
4. **edge_ambiguous_request** (опционально) — неоднозначный запрос

**Детали реализации:**
```json
{
  "eval_set_id": "orchestrator_routing_v1",
  "description": "Tests orchestrator routing logic to sub-agents",
  "eval_cases": [
    {
      "eval_id": "happy_routing_to_summarizer",
      "conversation": [
        {
          "user_content": {
            "role": "user",
            "parts": [
              { "text": "CONTEXT: chat_id='eval_orchestrator'\nSummarize the chat" }
            ]
          },
          "intermediate_data": {
            "intermediate_responses": [
              [
                "chat_summarizer",
                [{"text": "..."}]
              ]
            ]
          }
        }
      ]
    }
  ]
}
```

**ВАЖНО:** 
- Каждый кейс должен иметь комментарии в `description` поля
- Использовать `CONTEXT: chat_id='...'` prefix как в существующих тестах

---

### 2. Chat Summarizer Eval Test Cases

**Папка:** `tests/agents/eval/chat_summarizer/`

**Файлы:**
- `summarization_eval.evalset.json`
- `test_config.json`

**Кейсы (3-4 штуки):**

1. **happy_small_limit** — суммаризация с limit=10 сообщений
2. **happy_medium_limit** — суммаризация с limit=50 сообщений
3. **edge_empty_chat** — запрос на summary пустого чата → "No messages found"
4. **happy_with_time_filter** (опционально) — суммаризация с фильтром `since`

**Детали:**
- Проверять вызов `fetch_messages` tool с правильными параметрами
- Проверять вызов `simple_summarizer` sub-agent после получения сообщений

---

### 3. Seed Database для Eval

**Файл:** `tests/agents/eval/seed_eval_db.py` (уже существует)

**Обновить его:**
- Добавить seed данные для `eval_orchestrator` chat_id
- Добавить seed данные для `eval_chat_summarizer` chat_id
- 10-15 тестовых сообщений на каждый chat_id

**Пример:**
```python
# SEED DATA: For orchestrator eval
# Purpose: Test routing to chat_summarizer
messages_orchestrator = [
    Message(
        source="telegram",
        chat_id="eval_orchestrator",
        author_id="user1",
        author_nick="alice",
        content="Let's discuss the project roadmap",
        created_at=base_time
    ),
    # ... ещё 9-14 сообщений
]
```

---

### 4. Обновить README.md

Добавить секцию "## Evaluation Results" после "## Key ADK Concepts Demonstrated":

```markdown
## Evaluation

The project includes comprehensive ADK eval test cases for all agents:

```bash
# Run all evaluation tests
make eval

# Run specific agent eval
adk eval tests/agents/eval/orchestrator
adk eval tests/agents/eval/chat_summarizer
adk eval tests/agents/eval/chat_observer
```

**Coverage:**
- ✅ Orchestrator: routing logic, silent mode
- ✅ Chat Summarizer: fetch + summarization pipeline  
- ✅ Chat Observer: tool usage, filters

See `tests/agents/eval/*/` for test cases.
```

---

### 5. Добавить Makefile target

```makefile
.PHONY: eval
eval:
	@echo "Running ADK Evaluation Tests..."
	adk eval tests/agents/eval/orchestrator
	adk eval tests/agents/eval/chat_summarizer
	adk eval tests/agents/eval/chat_observer
```

## Требования к коду

**КРИТИЧНО:** Код должен содержать **много комментариев**, объясняющих:
- Что тестирует каждый eval_case
- Почему выбраны именно эти параметры
- Какие intermediate_responses ожидаются и почему

**Пример:**
```json
{
  "eval_id": "happy_routing_to_summarizer",
  "description": "TEST: Orchestrator должен распознать summary request и передать в chat_summarizer. Проверяем: 1) правильный sub-agent вызван 2) промежуточный ответ от summarizer получен",
  ...
}
```

## Напоминание: Это MVP!

- **Не нужно:** 100% покрытие всех edge cases
- **Нужно:** Продемонстрировать судьям, что eval framework используется
- **Достаточно:** 3-4 кейса на агента (happy path + 1 edge case)
- **Фокус:** Качество комментариев > количество тестов

## Definition of Done

- [ ] Изучена документация ADK Eval и существующие примеры
- [ ] Создан `tests/agents/eval/orchestrator/routing_eval.evalset.json` (3-4 кейса)
- [ ] Создан `tests/agents/eval/chat_summarizer/summarization_eval.evalset.json` (3-4 кейса)
- [ ] Обновлён `tests/agents/eval/seed_eval_db.py` с данными для новых eval
- [ ] Все eval кейсы содержат подробные комментарии в `description`
- [ ] Добавлен `make eval` target в Makefile
- [ ] README.md обновлён (секция Evaluation Results)
- [ ] `make eval` проходит успешно для всех трёх агентов
