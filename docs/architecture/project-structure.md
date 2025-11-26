# Структура Проекта Mesh Mind

Высокоуровневая структура каталогов проекта. Агенты должны придерживаться этой архитектуры.

---

## Общая Структура

```text
.
├── AGENTS.md                   # Правила для AI-агентов (навигатор)
├── README.md                   # Общее описание проекта
├── requirements.txt            # Python зависимости
├── Makefile                    # Команды для запуска
├── .env                        # Конфигурация (в .gitignore)
│


├── agent_template/             # Правила и workflows (переименовать в .agent/)
│   ├── rules/                  # Правила для агентов
│   └── workflows/              # Автоматизированные процессы
│
├── docs/                       # Документация проекта
│   ├── requirements/           # Продуктовые и технические требования
│   ├── architecture/           # Архитектурная документация
│   └── antigravity-rules-reglament.md
│
├── specs/                      # Атомарные спецификации (Specs)
│
├── ai_core/                    # Основной сервис (The Core)
│   ├── api/                    # API (FastAPI)
│   ├── ui/                     # Admin UI (Streamlit)
│   ├── agents/                 # AI-агенты (Google ADK)
│   ├── rag/                    # База знаний и векторы
│   ├── storage/                # Работа с БД
│   ├── ingest/                 # Загрузка данных
│   └── common/                 # Общие утилиты
│
├── telegram_bot/               # Telegram бот (отдельное приложение)
│
├── cli/                        # CLI-инструменты
│
├── tests/                      # Тесты
│   ├── agents/                 # Тесты агентов
│   │   └── eval/               # ADK eval тесты
│   ├── integration/            # Интеграционные тесты
│   └── unit/                   # Unit тесты
│
└── data/                       # Локальное хранилище (в .gitignore)
    ├── db/                     # SQLite файлы
    ├── vector_store/           # ChromaDB
    └── media/                  # Медиа файлы
```

---

## Описание Каталогов

### Корневые Файлы

- **`AGENTS.md`** — навигатор по правилам для AI-агентов
- **`README.md`** — общее описание проекта (пока пустой)
- **`requirements.txt`** — Python зависимости
- **`Makefile`** — команды для запуска сервисов
- **`.env`** — конфигурация (API ключи, токены)

### `agent_template/` (переименовать в `.agent/`)

- **`rules/`** — правила разработки для агентов
  - `01-project-overview.md` — обзор проекта
  - `02-architecture.md` — архитектурные принципы
  - `03-code-style.md` — стиль кода
  - `04-testing.md` — требования к тестам
  - `05-safety.md` — безопасность и git

- **`workflows/`** — автоматизированные процессы
  - `pr-check.md` — проверка перед коммитом
  - `check-rules.md` — проверка правил
  - `check-docs.md` — проверка документации
  - `test-agent.md` — тестирование агентов
  - `implement-from-spec.md` — реализация по спецификации

### `docs/`

**Документация проекта:**

- **`requirements/`** — требования
  - `product-vision.md` — продуктовое видение
  - `multi-agent-system.md` — требования к агентам
  - `technical-requirements.md` — технические требования

- **`architecture/`** — архитектура
  - `system-overview.md` — обзор системы
  - `multi-agent-design.md` — дизайн агентов
  - `project-structure.md` — этот файл

- **`antigravity-rules-reglament.md`** — регламент по организации документации

### `ai_core/`

**Сердце приложения** — вся бизнес-логика, API и UI:

- **`api/`** — FastAPI эндпоинты
  - `/ingest` — загрузка данных
  - `/chat/message` — обработка сообщений
  - `/summary`, `/ask` — команды

- **`ui/`** — Streamlit интерфейс
  - Просмотр БЗ
  - Редактирование документов
  - Поиск

- **`agents/`** — AI-агенты (Google ADK)
  - `orchestrator/` — главный координатор
  - `chat_summarizer/` — суммаризация
  - `qa/` — вопросы-ответы
  - `chat_observer/` — поиск сообщений
  - `summarizer/` — простой суммаризатор

- **`rag/`** — работа с базой знаний
  - ChromaDB интеграция
  - Векторный поиск

- **`storage/`** — работа с БД
  - SQLite интеграция
  - Модели данных

- **`ingest/`** — загрузка данных
  - Парсеры (email, документы, голосовые)
  - Транскрипция

- **`common/`** — общие утилиты
  - Конфигурация
  - Модели данных
  - Вспомогательные функции

### `telegram_bot/`

**Отдельное приложение** для работы с Telegram API:
- Long Polling
- Обработка команд
- Передача сообщений в AI Core

### `cli/`

**CLI-инструменты** для административных задач:
- Массовая загрузка email
- Массовая загрузка документов
- Утилиты для разработчиков

### `tests/`

**Тесты**:

- **`agents/eval/`** — ADK eval тесты для агентов
- **`integration/`** — интеграционные тесты
- **`unit/`** — unit тесты

### `data/`

**Локальное хранилище** (в `.gitignore`):

- **`db/`** — SQLite файлы
  - `chat_messages.db` — сообщения из Telegram

- **`vector_store/`** — ChromaDB
  - Векторные представления

- **`media/`** — медиа файлы
  - `voice/` — голосовые сообщения
  - `images/` — изображения
  - `docs/` — документы

---

## Соглашения

### Именование

- **Каталоги**: lowercase с подчеркиваниями (`ai_core`, `telegram_bot`)
- **Python модули**: lowercase с подчеркиваниями
- **Классы**: PascalCase (`QaAgent`, `ChatSummarizer`)
- **Функции**: snake_case (`fetch_messages`, `search_knowledge_base`)

### Импорты

- Относительные импорты внутри пакета
- Абсолютные импорты между пакетами:
  ```python
  from ai_core.storage.db import get_messages
  from ai_core.rag.knowledge_base import search
  ```

### Организация Кода

- Один агент = один каталог в `ai_core/agents/`
- Каждый агент экспортирует `agent` и `runner`
- Tools выносятся в отдельные модули

---

## Ссылки

- [Обзор Системы](./system-overview.md)
- [Дизайн Агентов](./multi-agent-design.md)
- [Правила Разработки](../../agent_template/rules/)
