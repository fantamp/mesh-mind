# Правила для AI-Агентов

## О Проекте

**Mesh Mind** — интеллектуальный ассистент с мультиагентной архитектурой на основе Google ADK.

Основные возможности: умное запоминание, суммаризация, вопросы-ответы на базе знаний.

## Где Находятся Правила

Все правила для работы агентов находятся в папке **`.agent/rules/`**:

1. **[01-project-overview.md](.agent/rules/01-project-overview.md)** — обзор проекта и ссылки на документацию
2. **[02-architecture.md](.agent/rules/02-architecture.md)** — архитектурные принципы и паттерны
3. **[03-code-style.md](.agent/rules/03-code-style.md)** — стиль кода и языки
4. **[04-testing.md](.agent/rules/04-testing.md)** — требования к тестированию (adk web, adk eval, pytest)
5. **[05-safety.md](.agent/rules/05-safety.md)** — безопасность и git

## Workflows

Автоматизированные процессы в **`.agent/workflows/`**:

- **[pr-check.md](.agent/workflows/pr-check.md)** — проверка перед коммитом
- **[check-docs.md](.agent/workflows/check-docs.md)** — проверка и обновление документации

## Детальная Документация

Полная документация проекта в **`docs/`**:

### Требования
- [docs/requirements/product-vision.md](docs/requirements/product-vision.md)
- [docs/requirements/multi-agent-system.md](docs/requirements/multi-agent-system.md)
- [docs/requirements/technical-requirements.md](docs/requirements/technical-requirements.md)

### Архитектура
- [docs/architecture/system-overview.md](docs/architecture/system-overview.md)
- [docs/architecture/multi-agent-design.md](docs/architecture/multi-agent-design.md)
- [docs/architecture/project-structure.md](docs/architecture/project-structure.md)

### Регламент
- [docs/antigravity-rules-reglament.md](docs/antigravity-rules-reglament.md) — правила организации документации

## Важно

> **Примечание**: Папка `.agent/` создана как `agent_template/` из-за ограничений Antigravity.  
> После проверки содержимого переименуй `agent_template/` → `.agent/`.

Тогда все ссылки в этом файле будут работать правильно.
