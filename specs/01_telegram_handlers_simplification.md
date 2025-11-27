# Спека 01: Упрощение Telegram Handlers

## Цель
Упростить функциональность Telegram бота, оставив только базовое сохранение сообщений и работу с Orchestrator.

## Изменения в telegram_bot/handlers.py

### 1. Команды
- **Оставить:** `/start` и `/help`
- **Удалить:** `/summary` и `/ask` (функция `summary_command`, `ask_command`)
- Обновить текст `/help` команды, убрав упоминания удалённых команд

### 2. Обработка форвардов
- **Удалить:** Всю логику автоматической суммаризации при форвардинге
- **Удалить:** Функции `forward_summary_job`, `schedule_forward_summary`
- **Удалить:** Состояние `forward_pool` из `context.chat_data`
- **Удалить:** Debounce таймер на 5 секунд
- Форвардные сообщения должны просто сохраняться в SQLite через стандартный flow

### 3. Конфиг для молчаливого режима
- Добавить параметр в `ai_core/common/config.py`: `BOT_SILENT_MODE: bool = False`
- Если `BOT_SILENT_MODE=True`: бот не отправляет никаких подтверждений
- Если `BOT_SILENT_MODE=False`: при сохранении писать "saved (текст сообщения)"
- Параметр можно переопределить через переменную окружения `BOT_SILENT_MODE` в `.env`

### 4. Обработка текстовых и голосовых сообщений
- Упростить `handle_text_message` и `handle_voice_message`
- Удалить проверки на `forward_pool` и форварды
- Оставить только: сохранение в SQLite → передача в Orchestrator → ответ пользователю

## Изменения в ai_core/

### 5. Удаление VectorDB (ChromaDB)
- **Удалить:** `ai_core/rag/` (вся папка)
- **Удалить:** `ai_core/tools/knowledge_base.py` (если существует)
- Удалить все импорты ChromaDB из кода
- Удалить из `requirements.txt`: `chromadb` и связанные зависимости
- **Важно:** Миграция и сохранение данных из VectorDB **не требуются**

### 6. Объединение qa агента в chat_observer
- **Удалить:** `ai_core/agents/qa/` (вся папка)
- **Обновить:** `ai_core/agents/chat_observer/agent.py`
  - Добавить функциональность ответов на вопросы (из qa агента)
  - Расширить `instruction` для обработки вопросов и поиска
  - Оставить только `fetch_messages` tool (без векторного поиска)
- **Обновить:** `ai_core/agents/orchestrator/agent.py`
  - Удалить импорт `qa_agent`
  - Удалить `qa_agent` из `sub_agents`
  - Обновить инструкции роутинга

## Обновление тестов
- Удалить тесты для `/summary` и `/ask` команд из `tests/test_telegram_bot.py`
- Удалить тесты для `qa_agent` из `tests/test_qa_agent.py`
- Обновить тесты для `chat_observer` с учётом новой функциональности
- Удалить тесты для VectorDB из `tests/test_vector.py`

## Обновление документации
- **Обновить:** `docs/requirements/multi-agent-system.md` - убрать упоминания VectorDB, qa_agent
- **Обновить:** `docs/architecture/system-overview.md` - убрать ChromaDB из схемы
- **Обновить:** `README.md` - описать новую упрощённую архитектуру
- **Примечание:** Изменения для `.agent/rules/` описаны в спеке `04_update_rules.md`
