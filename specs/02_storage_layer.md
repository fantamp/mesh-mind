# Спецификация: Слой Хранения (SQLite & ChromaDB)

## Цель
Настроить постоянное хранилище для сообщений (SQLite) и векторную базу знаний (ChromaDB).

## Требования
1.  **Схема SQLite:**
    *   Файл базы данных: `data/db/mesh_mind.db`
    *   Таблица `messages`:
        *   `id` (INTEGER PRIMARY KEY)
        *   `source` (TEXT) - например, 'telegram', 'email'
        *   `content` (TEXT)
        *   `timestamp` (DATETIME)
        *   `media_path` (TEXT, nullable)
        *   `meta_json` (TEXT) - для дополнительных полей, таких как sender_id, chat_id
2.  **Настройка ChromaDB:**
    *   Инициализировать персистентный клиент в `data/vector_store`.
    *   Создать коллекцию `knowledge_base`.
    *   Определить функцию эмбеддинга (используя Google Gemini или стандартный sentence-transformers).

## Верификация
*   [ ] Запустить скрипт для создания таблицы SQLite и проверить её существование через `sqlite3`.
*   [ ] Запустить python скрипт для инициализации ChromaDB и добавления тестового документа, затем выполнить запрос для проверки сохранения.
