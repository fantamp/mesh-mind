# Mesh Mind

Intelligent agentic system for Telegram chat analysis and automation.

## Features

- **Telegram Bot**: Captures text and voice messages.
- **AI Core**:
    - **Orchestrator**: Routes requests to specialized agents.
    - **Chat Summarizer**: Summarizes chat history.
    - **Chat Observer**: Finds specific messages and answers questions based on chat history.
- **Privacy**: Strict chat isolation.

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

## Documentation

- [System Overview](docs/architecture/system-overview.md)
- [Multi-Agent System Requirements](docs/requirements/multi-agent-system.md)
