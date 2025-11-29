# Mesh Mind

Intelligent agentic system for Telegram chat analysis and automation.

## Features

- **Telegram Bot**: Captures text and voice messages.
- **AI Core**:
    - **Orchestrator**: Routes requests to specialized agents.
    - **Chat Summarizer**: Summarizes chat history.
    - **Chat Observer**: Finds specific messages and answers questions based on chat history.
- **Privacy**: Strict chat isolation.

## Демонстрация Ключевых Концепций ADK

✅ **Мульти-агентная Система**: Оркестратор координирует специализированных субагентов
✅ **Пользовательские Инструменты**: `fetch_messages` с продвинутой фильтрацией
✅ **Сессии и Память**: InMemorySessionService с поддержкой stateful/stateless паттернов
✅ **Оценка Агентов (Eval)**: ADK eval framework с полным покрытием тестами
✅ **Наблюдаемость**: Структурированное логирование через loguru

## Architecture

- **Language**: Python 3.10+
- **Frameworks**: Google ADK, python-telegram-bot
- **Database**: SQLite
- **Models**: Gemini 2.5 Flash

## Getting Started

1. **Install dependencies**:
   ```bash
   make install
   ```

2. **Run Telegram Bot**:
   ```bash
   make bot
   ```

3. **Быстрое Демо** (без настройки Telegram):
   ```bash
   make demo
   ```
   Запускает автономную демонстрацию мульти-агентной системы.

## Documentation

- [System Overview](docs/architecture/system-overview.md)
- [Multi-Agent System Requirements](docs/requirements/multi-agent-system.md)
