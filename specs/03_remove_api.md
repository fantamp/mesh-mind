# Спека 03: Удаление API и Прямая Интеграция

## Цель
Удалить FastAPI слой и перевести Telegram Bot на прямой импорт модулей из `ai_core`.

## Удаление API

### 1. Удалить файлы
- **Удалить:** `ai_core/api/` (вся папка)
- Это включает:
  - `ai_core/api/main.py`
  - `ai_core/api/routers/`
  - `ai_core/api/models.py`
  - `ai_core/api/dependencies.py`

### 2. Обновить зависимости
- **Удалить из `requirements.txt`:**
  - `fastapi`
  - `uvicorn`
  - `pydantic` (если не используется в других местах)

## Прямая интеграция в Telegram Bot

### 3. Обновить telegram_bot/
- **Удалить:** `telegram_bot/api_client.py` (больше не нужен HTTP клиент)
- **Обновить:** `telegram_bot/handlers.py`
  - Заменить вызовы `api_client.*` на прямые импорты:
    - `from ai_core.storage.db import save_message, get_messages`
    - `from ai_core.common.transcription import TranscriptionService`
    - `from ai_core.agents.orchestrator.agent import root_agent as orchestrator`
  - Убрать функцию `get_api_client()`
  - Вызывать Orchestrator напрямую через ADK
  - Сохранять сообщения напрямую в SQLite

### 4. Обновить telegram_bot/bot.py
- Убрать инициализацию `api_client` в `bot_data`
- Инициализировать необходимые сервисы напрямую (например, `TranscriptionService`)

## Обновление конфигурации

### 5. Обновить Makefile
- **Удалить:** `make run-api` (или аналогичные команды для FastAPI)
- **Оставить:** `make run-bot`, `make test`, `make install`

### 6. Обновить .gitignore
- Можно убрать упоминания API-специфичных файлов (если есть)

## Обновление тестов

### 7. Удалить тесты
- **Удалить:** `tests/test_api.py`
- **Обновить:** `tests/test_telegram_bot.py`
  - Переписать тесты с учётом прямых импортов
  - Мокировать `ai_core` модули вместо HTTP запросов

## Обновление документации

### 8. Обновить документацию
- **Обновить:** `docs/architecture/system-overview.md`
  - Убрать "API Server (FastAPI)" из схемы
  - Обновить диаграмму: Telegram Bot → напрямую AI Core
  - Убрать описание endpoints
- **Обновить:** `README.md`
  - Убрать инструкции по запуску API
  - Описать упрощённую архитектуру
- **Примечание:** Изменения для `.agent/rules/` описаны в спеке `04_update_rules.md`
