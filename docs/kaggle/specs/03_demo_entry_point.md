# Спека: Демонстрационный Entry Point

## Цель
Создать простой демо-скрипт для быстрой демонстрации возможностей Multi-agent системы без развертывания Telegram бота.

**Impact:** Technical Implementation (50 баллов) + Documentation (20 баллов)

## Задача

Создать демо-скрипт, который демонстрирует работу всех ключевых компонентов системы.

### Структура файлов

```
scripts/
└── demo/
    ├── __init__.py
    └── demo_agents.py
```

### Функциональность `demo_agents.py`

Скрипт должен:

1. **Инициализация тестовой БД**
   - Создать временную test database в памяти или `data/db/demo_chat.db`
   - Заполнить её примерами сообщений (10-15 штук)
   - Сообщения на разных языках (русский, английский, украинский)
   - Разные авторы (@alice, @bob, @charlie)

2. **Демонстрация Orchestrator**
   
   Запустить 3 демо-запроса:
   
   **a) Summary request** (роутинг → chat_summarizer):
   ```
   USER: Summarize the last 10 messages
   EXPECTED: Orchestrator → chat_summarizer → краткое саммари
   ```
   
   **b) Search request** (роутинг → chat_observer):
   ```
   USER: Find messages from @alice about Python
   EXPECTED: Orchestrator → chat_observer → список сообщений
   ```
   
   **c) Silent mode test** (casual message):
   ```
   USER: Hello everyone, how are you doing?
   EXPECTED: Orchestrator → "null" или пустой ответ (не отвечает на casual chat)
   ```

3. **Форматированный вывод**
   - Использовать цветной вывод (например, через `colorama` или emoji)
   - Показывать: запрос → какой агент выбран → результат
   - Время выполнения для каждого запроса

### Пример структуры вывода

```
========================================
  MESH MIND: Multi-Agent Demo
========================================

📦 Initializing test database...
   ✓ Created 15 test messages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TEST 1] Summary Request
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 USER: "Summarize the last 10 messages"
🤖 ORCHESTRATOR: Routing to → chat_summarizer
📊 RESULT: [саммари текст...]
⏱️  Completed in 2.3s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TEST 2] Search Request
...
```

### Требования к реализации

1. **Standalone скрипт**: не требует запущенного Telegram бота
2. **Self-contained**: автоматически создаёт тестовые данные
3. **Понятный код**: много комментариев, объясняющих каждый шаг
4. **Обработка ошибок**: graceful handling, понятные сообщения об ошибках
5. **Быстрый запуск**: всё должно выполняться за < 30 секунд

### Добавить в Makefile

Добавить новый target:

```makefile
.PHONY: demo
demo:
	@echo "Running Multi-Agent Demo..."
	python scripts/demo/demo_agents.py
```

### Обновить документацию

В `README.md` добавить в секцию "## Getting Started":

```markdown
3. **Quick Demo** (without Telegram setup):
   ```bash
   make demo
   ```
   
   This runs a standalone demo showcasing the multi-agent system.
```

## Definition of Done

- [ ] Создан `scripts/demo/demo_agents.py` с функциональностью описанной выше
- [ ] Скрипт работает standalone (без Telegram)
- [ ] Демонстрирует все 3 кейса (summary, search, silent mode)
- [ ] Форматированный вывод с визуальным разделением
- [ ] Добавлен `make demo` target в Makefile
- [ ] README.md обновлён (добавлена секция Quick Demo)
- [ ] Код содержит достаточно комментариев для понимания
