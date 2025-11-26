# Требования к Тестированию

## Общий Принцип

После реализации функциональности **обязательно** создавать тесты.

## Тестирование AI-Агентов

### 1. Ручное Тестирование: `adk web`

Запускает Web UI для интерактивного тестирования агентов:

```bash
make adk-web
```

- Открывается браузер на `http://localhost:8000`
- Можно выбрать агента и отправить тестовые запросы
- Посмотреть траекторию выполнения (какие tools вызывались)
- Сохранить сессию для воспроизведения

**Когда использовать**: для отладки агента, проверки граничных случаев, создания "golden path" сценариев.

**Документация**: https://google.github.io/adk-docs/evaluation/

### 2. Автоматическое Тестирование: `adk eval`

Запускает автоматизированные тесты на основе `.evalset.json` файлов:

```bash
adk eval tests/agents/eval/
```

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

**Критерии оценки** (встроенные в ADK):
- `tool_trajectory_correctness` — правильность последовательности tool calls
- `response_contains_keywords` — наличие ключевых слов в ответе
- `response_quality_rubric` — LLM-based оценка качества
- `response_exact_match` — точное совпадение с ожидаемым ответом

**Когда использовать**: для CI/CD, регрессионного тестирования, проверки качества агентов.

**Документация**: https://google.github.io/adk-docs/evaluation/

### 3. Unit Тесты: pytest

Используется для тестирования отдельных компонентов и интеграций:

```bash
pytest tests/
```

**Что тестировать**:
- Отдельные функции и классы
- Интеграцию между компонентами
- Граничные случаи

## Требования к Покрытию

- Критичные функции: обязательное покрытие тестами
- AI-агенты: минимум eval тесты + ручная проверка через `adk web`
- Инфраструктурный код: unit тесты где возможно

## Стратегия Тестирования

1. **Разработка** → ручное тестирование через `adk web`
2. **После работы логики** → создание eval тестов
3. **Для компонентов** → unit тесты через pytest
4. **CI/CD** → автоматический запуск `adk eval` и `pytest`

## Полезные Ссылки

> Пути относительно корня проекта

- [ADK Evaluation Guide](https://google.github.io/adk-docs/evaluation/)
- [Evaluation Criteria](https://google.github.io/adk-docs/evaluation/criteria/)
- docs/requirements/technical-requirements.md#тестирование-агентов
