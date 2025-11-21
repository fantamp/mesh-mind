# Specification: Telegram Bot (telegram_bot)

## 1. Overview
This is a standalone Python application that interfaces with the Telegram Bot API. It handles user interactions and forwards data to the AI Core API.

## 2. Requirements

### 2.1. Framework

**Выбранная библиотека:** `python-telegram-bot` версии **20.x** (асинхронная)

**Обоснование выбора:**

После тщательного анализа двух основных библиотек (`python-telegram-bot` и `aiogram`), для данного MVP проекта выбрана **`python-telegram-bot` v20+** по следующим причинам:

1. **Зрелость и стабильность**: PTB — проверенная временем библиотека («veteran») с отличной стабильностью и комплексным покрытием всех возможностей Telegram Bot API
2. **Огромное сообщество**: Самая большая база пользователей в мире, множество примеров кода, активная поддержка в Telegram-группе, Stack Overflow, GitHub Discussions
3. **Отличная документация**: Исчерпывающая документация, Wiki с подробными гайдами, официальные примеры для разных сценариев
4. **Полная асинхронность (v20+)**: С версии 20.0 (2022) библиотека полностью переписана на `asyncio`, обеспечивая высокую производительность и соответствие современным стандартам
5. **MVP-friendly**: Простота настройки, большое количество готовых примеров (echobot, conversationbot), что ускоряет разработку
6. **Соответствие требованиям проекта**: Для базового функционала (получение сообщений, команды `/start`, `/summary`, `/ask`) не требуется сложная FSM — встроенных возможностей PTB достаточно

**Альтернатива (не выбрана):** `aiogram` v3 — современный фреймворк с нативной асинхронностью, встроенной FSM и высокой производительностью. Отличный выбор для проектов с высокими нагрузками и сложными диалоговыми сценариями, но для MVP избыточен и имеет меньше англоязычных примеров.

**Конфигурация:**
-   Telegram Bot Token берётся из переменной окружения `.env`
-   Режим работы: **Long Polling** (для упрощения деплоя в MVP фазе)

### 2.2. Message Handling
-   **Text Messages:**
    -   Send to `POST /ingest` (API).
-   **Voice Messages:**
    -   Download file locally.
    -   Send to `POST /ingest` (API) with `file` field.
-   **Images:**
    -   **Ignore** or reply "Images are not supported yet". *Decision: Ignore to avoid spamming the chat, or log debug message.*

### 2.3. Commands
-   `/start`: Welcome message.
-   `/summary`:
    -   Call `POST /summarize` (API).
    -   Send result to chat.
-   `/ask <question>`:
    -   Call `POST /ask` (API).
    -   Send result to chat.

### 2.4. Resilience
-   Long Polling mode.
-   Auto-reconnect on network failure.
-   Log errors but don't crash the main loop.

## 3. Implementation Details

### 3.1. Структура проекта
-   **Файл:** `telegram_bot/main.py` — основной модуль бота
-   **Зависимости:**
    -   `python-telegram-bot>=20.0` — основная библиотека
    -   `httpx` — для асинхронных HTTP-запросов к AI Core API
    -   `python-dotenv` — для загрузки токена из `.env`

### 3.2. Основные компоненты

**Application setup:**
```python
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import httpx
import os

# Инициализация
app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
```

**HTTP-клиент для AI Core API:**
-   Использовать `httpx.AsyncClient` для всех запросов к `http://localhost:8000/api/...`
-   Реализовать retry-логику для resilience (например, с `tenacity`)

**Handlers:**
-   `CommandHandler` для `/start`, `/summary`, `/ask`
-   `MessageHandler(filters.TEXT)` для текстовых сообщений
-   `MessageHandler(filters.VOICE)` для голосовых сообщений
-   Long Polling через `app.run_polling()`

## 4. Verification & Definition of Done
-   [ ] Bot starts and connects to Telegram.
-   [ ] Text message is received and sent to API (verify via API logs).
-   [ ] Voice message is transcribed and text is saved (verify via DB).
-   [ ] `/summary` returns a response.
-   [ ] `/ask` returns a response.
-   [ ] **Manual Test:** Run the bot, send "Hello", check if it appears in SQLite `messages` table.

## 5. Дополнительные ресурсы

### python-telegram-bot (v20+)
-   [Официальная документация](https://docs.python-telegram-bot.org/) — основной источник информации по библиотеке версии 20.x
-   [API Reference](https://docs.python-telegram-bot.org/en/stable/telegram.html) — полная документация по всем классам и методам
-   [Примеры кода](https://docs.python-telegram-bot.org/en/stable/examples.html) — **обязательно изучи** официальные примеры:
    -   `echobot.py` — базовый пример эхо-бота (начни с него!)
    -   `conversationbot.py` — пример бота с многошаговыми диалогами
    -   `timerbot.py` — использование JobQueue для отложенных сообщений
-   [GitHub Repository](https://github.com/python-telegram-bot/python-telegram-bot) — репозиторий с примерами и issues
-   [Wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki) — подробные гайды и best practices
-   [Telegram Group](https://t.me/pythontelegrambotgroup) — активное сообщество для вопросов и помощи
-   [Stack Overflow Tag](https://stackoverflow.com/questions/tagged/python-telegram-bot) — для технических вопросов

**Ключевые особенности v20:**
-   Полностью построена на `asyncio` (с 2022 года)
-   Все callback-функции должны быть `async def`
-   Все вызовы Bot API требуют `await`
-   По умолчанию использует `httpx` для сетевых операций
-   Поддерживает Python 3.10+

### httpx (для HTTP-запросов к AI Core API)
-   [Официальная документация](https://www.python-httpx.org/) — основной ресурс
-   [Async Support](https://www.python-httpx.org/async/) — **критически важный раздел** для асинхронных запросов с `AsyncClient`
-   [Developer Interface](https://www.python-httpx.org/api/) — детальная API reference

**Пример использования:**
```python
async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8000/api/ingest", json={"text": message})
```

### Дополнительные инструменты
-   [python-dotenv](https://pypi.org/project/python-dotenv/) — для загрузки переменных окружения из `.env`
-   [tenacity](https://pypi.org/project/tenacity/) — для retry-логики при API вызовах
