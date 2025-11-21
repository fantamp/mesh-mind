# Specification: QA Agent (ai_core/agents)

## 1. Overview
Агент для ответов на вопросы пользователя на основе базы знаний (Vector DB) и истории чата. Реализует паттерн RAG (Retrieval Augmented Generation) с использованием Google Agent Development Kit (ADK).

## 2. Requirements

### 2.1. Core Logic (ADK)
-   **Framework:** Google Agent Development Kit (ADK) — используй класс `google.adk.agents.LlmAgent` (или `Agent`)
-   **Model:** `Settings.GEMINI_MODEL_SMART` (например, `gemini-2.5-pro`)
-   **Input:** Вопрос пользователя (строка)
-   **Output:** Текстовый ответ со ссылками на источники в формате `(источник: filename)`

**Обязательные параметры агента:**
-   `name` — уникальное имя агента (например, `"qa_agent"`)
-   `model` — модель из настроек (`Settings.GEMINI_MODEL_SMART`)
-   `instruction` — системный промпт с инструкциями по RAG и источникам
-   `description` — краткое описание назначения агента
-   `tools` — список инструментов, включая custom tool для поиска в Vector Store

### 2.2. RAG Flow

#### 1. Retrieval (Поиск)
-   **Custom Tool:** Создать функцию `search_knowledge_base(query: str) -> str`
-   **Функция делает:**
    1.  Вызывает `VectorStore.search(query, top_k=5)` для поиска релевантных чанков
    2.  Возвращает найденные чанки в текстовом формате с метаданными (filename, chunk_id)
-   **Передать в параметр `tools`** агента, чтобы ADK мог её вызывать

#### 2. Augmentation (Дополнение контекста)
-   ADK автоматически встроит результаты tool в контекст
-   **Системный Prompt (в `instruction`)** должен содержать:
    ```
    You are a helpful AI assistant. Answer user questions based ONLY on the provided context 
    from the knowledge base. 
    
    CRITICAL RULES:
    - If the answer is not in the provided context, respond with "Я не знаю"
    - Do NOT hallucinate or make up information
    - ALWAYS cite sources in the format: (источник: filename)
    - Provide clear and concise answers in the same language as the question
    ```

#### 3. Generation (Генерация ответа)
-   ADK вызовет LLM с контекстом из tool
-   Модель сгенерирует ответ, следуя инструкциям из `instruction`

### 2.3. Source Attribution (Атрибуция источников)
-   **Формат:** Текстовый ответ с встроенными ссылками
-   **Пример:** `"Столица Франции — Париж (источник: geography.pdf, message_123)"`
-   **Реализация:** Указать в `instruction`, что агент должен всегда указывать источники
-   Для MVP этого достаточно (YAGNI для structured output)

### 2.4. Session Management
-   **Использовать:** `InMemorySessionService` из ADK
-   **Обоснование:** Простота для MVP, можно позже переключиться на persistent storage

### 2.5. Agent и Runner Lifecycle
-   **Agent и Runner создаются один раз** при старте приложения (на уровне модуля)
-   Tool функция (`search_knowledge_base`) также определяется на уровне модуля

## 3. Implementation Details

### 3.1. Структура файла `ai_core/agents/qa.py`

```python
"""
QA Agent

Агент для ответов на вопросы на основе базы знаний (RAG pattern) используя Google ADK.
"""

import asyncio
import os
import uuid
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
from google.adk.models.google_llm import _ResourceExhaustedError

from ai_core.common.config import settings
from ai_core.rag.vector_store import VectorStore
from ai_core.common.logging import logger

# Устанавливаем API key для ADK
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Инициализируем Vector Store (подключение к ChromaDB)
_vector_store = VectorStore()

# Session service
_session_service = InMemorySessionService()


# Custom Tool: Поиск в базе знаний
def search_knowledge_base(query: str) -> str:
    """
    Ищет релевантную информацию в базе знаний.
    
    Args:
        query: Поисковый запрос пользователя
        
    Returns:
        Найденные чанки с метаданными в текстовом формате
    """
    logger.info(f"Поиск в базе знаний: {query}")
    
    try:
        # Ищем в векторной базе
        results = _vector_store.search(query, top_k=5)
        
        if not results:
            return "В базе знаний не найдено релевантной информации по этому запросу."
        
        # Форматируем результаты
        formatted_results = []
        for idx, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source", "unknown")
            text = result.get("text", "")
            formatted_results.append(f"[{idx}] (источник: {source})\n{text}")
        
        output = "\n\n".join(formatted_results)
        logger.debug(f"Найдено {len(results)} результатов")
        return output
        
    except Exception as e:
        logger.error(f"Ошибка при поиске в базе знаний: {e}")
        return f"Ошибка поиска: {str(e)}"


# Создаём агента с инструментом поиска
_qa_agent = LlmAgent(
    name="qa_agent",
    model=settings.GEMINI_MODEL_SMART,
    description="Отвечает на вопросы пользователя на основе базы знаний",
    instruction="""You are a helpful AI assistant. Answer user questions based ONLY on the provided context 
from the knowledge base.

CRITICAL RULES:
- If the answer is not in the provided context, respond with "Я не знаю"
- Do NOT hallucinate or make up information
- ALWAYS cite sources in the format: (источник: filename)
- Provide clear and concise answers in the same language as the question

Use the search_knowledge_base tool to find relevant information before answering.""",
    tools=[search_knowledge_base],  # Передаём custom tool
)

# Создаём runner
_qa_runner = Runner(
    agent=_qa_agent,
    app_name="agents", # Используем "agents" для соответствия структуре ADK
    session_service=_session_service,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        ResourceExhausted, InternalServerError, ServiceUnavailable, _ResourceExhaustedError, Exception
    )),
    reraise=True
)
def ask_question(question: str, user_id: str = "default_user") -> str:
    """
    Задаёт вопрос QA агенту.
    
    Args:
        question: Вопрос пользователя
        user_id: ID пользователя (для session management)
        
    Returns:
        Ответ агента со ссылками на источники
        
    Raises:
        ValueError: Если вопрос пустой
        Exception: При ошибках вызова API
    """
    if not question or not question.strip():
        raise ValueError("Вопрос не может быть пустым")
    
    logger.info(f"Получен вопрос от {user_id}: {question}")
    
    try:
        # Формируем сообщение пользователя
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=question)]
        )
        
        # Генерируем session_id
        session_id = f"qa_{user_id}_{uuid.uuid4()}"
        
        # Явно создаем сессию асинхронно перед использованием runner'а
        asyncio.run(_session_service.create_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        ))
        
        # Вызываем агента через runner
        response_text = None
        
        for event in _qa_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
        
        if not response_text:
            raise Exception("Агент не вернул ответ")
        
        logger.info(f"Ответ сгенерирован, длина: {len(response_text)} символов")
        return response_text
        
    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса: {e}")
        raise
```

### 3.2. Custom Tool Best Practices

-   **Docstring обязателен:** ADK использует docstring для формирования описания tool для LLM
-   **Типизация:** Используй type hints для параметров и возвращаемого значения
-   **Обработка ошибок:** Tool должен всегда возвращать строку, даже при ошибке
-   **Логирование:** Добавь логи для отладки

### 3.3. ADK Dependencies

Необходимые пакеты (добавить в `requirements.txt`):
```
google-adk>=0.1.0
tenacity
```

### 3.4. Resilience

-   **Rate Limiting:** Использовать `tenacity` для повторных попыток при ошибках 429 (Resource Exhausted).
-   **Session Management:** Использовать `asyncio.run` для явного создания сессий.

## 4. Verification & Definition of Done

-   [ ] Agent создаётся без ошибок при старте приложения
-   [ ] Custom tool `search_knowledge_base` работает корректно
-   [ ] Agent извлекает релевантные чанки для известного вопроса
-   [ ] Agent отвечает правильно, когда информация присутствует
-   [ ] **Agent отвечает "Я не знаю", когда информация отсутствует** (критический тест!)
-   [ ] Ответы содержат ссылки на источники в формате `(источник: filename)`
-   [ ] **Manual Test:** 
    1.  Заинджестить специфический факт (например, "Секретный код: 1234")
    2.  Спросить "Какой секретный код?" → Ожидаем "1234" с источником
    3.  Спросить "Какая погода на Марсе?" → Ожидаем "Я не знаю"

## 5. Дополнительные ресурсы

-   [ADK Documentation](https://google.github.io/adk-docs/)
-   [LLM Agents Guide](https://google.github.io/adk-docs/agents/llm-agents/)
-   [Custom Function Tools](https://google.github.io/adk-docs/tools-custom/function-tools/)
-   [ADK Python Repository](https://github.com/google/adk-python)
