# Правила написания writeup для Kaggle Submission

## Языки и лимиты
- **writeup.ru.md** — ведущий файл на русском языке, максимум 1400 слов
- **writeup.en.md** — английский перевод, максимум 1400 слов
- При изменении `writeup.ru.md` обязательно обновлять `writeup.en.md`

## Целевая аудитория и фокус
- Писать для **судей соревнования** с техническим background
- **Главный фокус:** демонстрация технической реализации ADK концептов (минимум 3)
- Второстепенный: описание проблемы и архитектуры решения

## Обязательные ADK концепты для демонстрации
- **Multi-agent system:** Orchestrator + Sub-agents (Chat Summarizer, Chat Observer)
- **Custom Tools:** fetch_messages с фильтрацией по chat_id/author/time
- **Sessions & Memory:** InMemorySessionService для сохранения контекста
- **Agent Evaluation:** ADK eval framework с метриками
