# Инструкция по ручному тестированию AI-агентов

## Обзор

В проекте два AI-агента на базе Google ADK:
- **QA Agent** - отвечает на вопросы по базе знаний
- **Summarizer Agent** - создаёт саммари чата

## Способ 1: Тестирование через ADK Web UI

ADK Web UI - это встроенный интерфейс от Google для разработки и отладки агентов.

### Запуск

```bash
make adk-web
```

Откроется браузер на `http://localhost:8000`

### Тестирование QA Agent

1. В верхнем меню выбери **`qa_agent`**
2. Задай вопрос в формате:
   ```
   CONTEXT: chat_id='-1003332243260' Question: What is in sample.md?
   ```

**Что проверить:**
- ✅ Агент вызывает tool `search_knowledge_base`
- ✅ Находит информацию из `data/sample_docs/`
- ✅ Отвечает на основе найденных документов
- ✅ Указывает источники (source)

**Другие примеры вопросов:**
- `CONTEXT: chat_id='-1003332243260' Question: What is mentioned in the sample documents?`
- `CONTEXT: chat_id='-1003332243260' Question: Summarize the content of sample.txt`

### Тестирование Summarizer Agent

1. В верхнем меню выбери **`summarizer_agent`**
2. Запроси саммари:
   ```
   Please summarize documents for chat_id='-1003332243260'
   ```

**Что проверить:**
- ✅ Агент вызывает tool `fetch_documents` или `fetch_chat_messages`
- ✅ Получает данные из базы
- ✅ Создаёт краткое саммари
- ✅ Саммари на корректном языке

**Другие примеры:**
- `Summarize chat history for chat_id='-1003332243260'`
- `Give me a summary of all documents in the knowledge base for chat_id='-1003332243260'`

---

## Способ 2: Тестирование через веб-интерфейс проекта

Streamlit UI - это пользовательский интерфейс проекта для работы с агентами.

### Запуск

```bash
make ui
```

Откроется браузер на `http://localhost:8501`

### Подготовка данных (первый запуск)

**Страница: Knowledge Base**

1. Перейди на страницу **"Knowledge Base"**
2. Используй форму загрузки файлов:
   - Загрузи файлы из `data/sample_docs/` (sample.txt, sample.md, sample.eml)
   - Или загрузи свои документы
3. Укажи `chat_id` (например: `test_chat`)
4. Нажми **"Ingest"**
5. Проверь, что файлы успешно добавлены

### Тестирование QA Agent

**Страница: Chat**

1. Перейди на страницу **"Chat"**
2. Укажи `chat_id` (тот же, что использовал при загрузке)
3. В поле вопроса напиши:
   ```
   What is mentioned in sample.md?
   ```
4. Нажми **"Ask Question"**

**Что проверить:**
- ✅ Агент находит информацию из загруженных документов
- ✅ Ответ релевантен вопросу
- ✅ Указаны источники информации

**Другие примеры вопросов:**
- `What topics are covered in the sample documents?`
- `Tell me about the content of sample.txt`
- `What information is in the email?`

### Тестирование Summarizer Agent

**Страница: Chat**

1. На той же странице **"Chat"**
2. Нажми кнопку **"Generate Summary"**
3. Дождись результата

**Что проверить:**
- ✅ Саммари содержит основные темы из документов
- ✅ Текст структурирован и читаем
- ✅ Саммари на правильном языке

---

## Тестирование с собственными данными

Ты можешь загрузить свои документы вместо/в дополнение к `sample_docs`:

**Поддерживаемые форматы:**
- `.txt` - текстовые файлы
- `.md` - Markdown
- `.pdf` - PDF документы
- `.eml` - Email файлы
- `.mp3`, `.ogg`, `.wav` - аудио файлы (с транскрипцией)

**Как загрузить:**
1. Через Streamlit UI (Knowledge Base)
2. Или через CLI:
   ```bash
   python cli/main.py ingest /path/to/your/docs --recursive
   ```

---

## Полезные команды

```bash
make adk-web  # ADK интерфейс для отладки агентов
make ui       # Streamlit UI для пользователей
make api      # REST API (для программного доступа)
make bot      # Telegram Bot
make test     # Запуск автотестов
```

## Очистка данных

Если нужно начать с чистой базы:

```bash
python scripts/clear_databases.py
```

Это удалит все сообщения, документы и векторные данные.
