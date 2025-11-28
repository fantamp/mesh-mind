# Kaggle Submission: Enterprise Agents Track

> **Трек**: Enterprise Agents  
> **Дедлайн**: 1 декабря 2025, 11:59 AM PT  
> **Философия**: MVP — просто, но эффективно

---

## Требования к Submission

### A. Технические Концепции ADK (минимум 3)

**Обязательные для демонстрации:**

1. **✅ Multi-agent system**
   - Orchestrator + Chat Summarizer + Chat Observer
   - Оркестрация через Sub-Agents pattern

2. **✅ Sessions & Memory**
   - `InMemorySessionService` для хранения контекста
   - `chat_id` = `session_id`
   - Агент помнит диалог

3. **✅ Custom Tools**
   - `fetch_messages` — получение сообщений из SQLite

4. **✅ LLM Reasoning**
   - Chat Observer ищет сообщения и отвечает на вопросы
   - Orchestrator понимает natural language

**Дополнительные (опционально)**:

5. **Evaluation** — `adk eval` тесты для агентов
6. **Agent Hierarchy** — Simple Summarizer через AgentTool

---

### B. Writeup (макс. 600 строк)

**Структура документа**:

#### 1. Business Problem
**Проблема**: Компании тонут в информации из email, чатов, документов. Поддержка тратит часы на поиск.

**Решение**: Mesh Mind — интеллектуальный ассистент, который автоматически запоминает всю информацию и помогает быстро находить ответы.

**Метрика успеха**: Время поиска с 2+ часов → 30 секунд.

#### 2. Why ADK?
- **Multi-Agent architecture** — специализированные агенты для разных задач
- **Easy integration** — Google ADK упрощает создание агентов
- **Built-in tools** — Sessions, Memory, Evaluation из коробки

#### 3. Architecture
- **Orchestrator** — центральный координатор (понимает natural language)
- **Chat Summarizer** — создает саммари истории чата
- **Chat Observer** — находит конкретные сообщения и отвечает на вопросы

**Схема взаимодействия**: См. [multi-agent-design.md](./architecture/multi-agent-design.md)

#### 4. ADK Concepts Used
1. **Sub-Agents Pattern** — LLM-driven delegation
2. **AgentTool Pattern** — инкапсуляция задач
3. **InMemorySessionService** — контекст диалога
4. **Custom Tools** — `fetch_messages`
5. **Evaluation** — `adk eval` для тестирования

#### 5. Results
- ✅ MVP работает для Telegram
- ✅ Изоляция по чатам (каждый чат видит только свои данные)
- ✅ Chat Observer: высокая точность поиска

#### 6. Future Work
- Кастомная суммаризация по инструкциям
- Confidence score для ответов
- Подключение других источников данных

---

### C. Технические Артефакты

**Обязательные файлы**:

1. **README.md**
   - Установка и запуск
   - Примеры использования
   - Скриншоты

2. **requirements.txt**
   - Все зависимости с версиями

3. **.env.example**
   - Шаблон конфигурации

4. **Demo Video** (макс. 5 минут)
   - Показать работу Orchestrator'а
   - Суммаризация чата
   - Chat Observer отвечает на вопросы
   - Демонстрация изоляции по чатам

5. **Eval Tests**
   - `tests/agents/eval/` с результатами
   - Score > 0.7 для всех агентов

---

### D. Бонусные Баллы (опционально)

1. **Production-ready deployment**
   - Не требуется для MVP

2. **Advanced evaluation metrics**
   - ✅ `adk eval` тесты созданы
   - Custom rubrics для оценки качества саммари

3. **Novel use of ADK features**
   - Natural language understanding без команд
   - Автоматическая обработка пересланных сообщений

4. **Clear documentation**
   - ✅ Полная документация в `docs/`
   - ✅ Walkthrough для разработчиков

---

### E. Submission на Kaggle

**Подготовка**:

1. Создать папку `kaggle/` в корне проекта
2. Скопировать туда:
   - README.md
   - requirements.txt
   - .env.example
   - Demo video
   - Writeup.md
   - Скриншоты

3. Упаковать:
   ```bash
   cd kaggle/
   zip -r mesh-mind-submission.zip *
   ```

4. Загрузить на Kaggle в разделе Enterprise Agents track

---

## Чек-Лист перед Submission

### Функциональность
- [ ] Orchestrator понимает natural language
- [ ] Chat Summarizer создает структурированные саммари
- [ ] Chat Observer находит сообщения и отвечает на вопросы
- [ ] Изоляция по чатам работает

### Тестирование
- [ ] Ручное тестирование через `adk web` пройдено
- [ ] `adk eval` тесты созданы (score > 0.7)
- [ ] `pytest` проходит без ошибок

### Документация
- [ ] README.md с инструкциями
- [ ] Writeup.md (макс. 1500 слов)
- [ ] Комментарии в коде на русском
- [ ] Демо видео записано (макс. 5 минут)

### Артефакты
- [ ] requirements.txt актуален
- [ ] .env.example создан
- [ ] Скриншоты работы системы
- [ ] Eval результаты сохранены

### Технические Концепции ADK
- [ ] Multi-agent system (3+ агента)
- [ ] Sessions & Memory (InMemorySessionService)
- [ ] Custom Tools (минимум 1 tool)
- [ ] Evaluation (`adk eval` тесты)

---

## Timing

**24-27 ноября**: Финальные доработки MVP
- Изоляция по чатам
- Whitelist чатов
- UI review

**28-29 ноября**: Подготовка submission
- Запись демо видео
- Написание writeup
- Создание README

**30 ноября**: Submission
- Упаковка файлов
- Загрузка на Kaggle
- Проверка перед дедлайном

**1 декабря 11:59 AM PT**: Дедлайн

---

## Полезные Ссылки

**Проектная документация**:
- [Продуктовое Видение](./requirements/product-vision.md)
- [Мультиагентная Система](./requirements/multi-agent-system.md)
- [Архитектура Агентов](./architecture/multi-agent-design.md)

**Kaggle**:
- [Enterprise Agents Track](https://www.kaggle.com/competitions/)
- [Submission Guidelines](https://www.kaggle.com/)

**Google ADK**:
- [Documentation](https://google.github.io/adk-docs/)
- [Examples](https://github.com/google/adk-python/tree/main/examples)
