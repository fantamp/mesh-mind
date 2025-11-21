# Specification: Summarizer Agent (ai_core/agents)

## 1. Overview
Агент для генерации краткого саммари истории чата. Использует Google Agent Development Kit (ADK) и модель Gemini для обработки пакета сообщений.

## 2. Requirements

### 2.1. Core Logic (ADK)
-   **Framework:** Google Agent Development Kit (ADK) — используй класс `google.adk.agents.LlmAgent` (или `Agent`)
-   **Model:** `Settings.GEMINI_MODEL_SMART` (например, `gemini-2.0-flash-exp` или `gemini-1.5-pro`)
-   **Input:** Список сообщений `List[Message]`, которые будут преобразованы в текстовый формат
-   **Output:** Markdown-форматированная строка с саммари

**Обязательные параметры агента:**
-   `name` — уникальное имя агента (например, `"summarizer_agent"`)
-   `model` — модель из настроек (`Settings.GEMINI_MODEL_SMART`)
-   `instruction` — системный промпт, определяющий поведение агента
-   `description` — краткое описание назначения агента

### 2.2. Functionality

**Функция `summarize(messages: List[Message]) -> str`:**

1.  **Валидация входных данных:**
    -   Проверить, что список `messages` не пустой
    -   Если пустой — вызвать `ValueError`

2.  **Преобразование в текст:**
    -   Превратить список `Message` в читаемый текст
    -   Формат: `"[YYYY-MM-DD HH:MM] Имя: Сообщение\n"`
    -   Пример:
      ```
      [2025-11-20 15:30] Иван: Привет!
      [2025-11-20 15:31] Мария: Как дела?
      ```

3.  **Вызов агента через Runner:**
    -   Использовать `Runner` для запуска агента
    -   Передать форматированный текст как сообщение пользователя
    -   Получить ответ от агента

4.  **Системный Prompt (в параметре `instruction`):**
    ```
    You are a helpful assistant. Summarize the following conversation concisely 
    in the same language as the conversation. Highlight key decisions and action items.
    Provide a well-structured summary in markdown format.
    ```

### 2.3. Context Window Management
-   **Стратегия:** Передаём все сообщения (или последние 1000, если очень много)
-   **Обоснование:** Gemini 1.5/2.0 имеет огромное контекстное окно (1M+ токенов), поэтому сложная обрезка не нужна для MVP (YAGNI)

### 2.4. Session Management
-   **Использовать:** `InMemorySessionService` из ADK
-   **Обоснование:** Простота для MVP, история не критична для summarizer

### 2.5. Agent и Runner Lifecycle
-   **Agent и Runner создаются один раз** при старте приложения (на уровне модуля)
-   Создавать новые экземпляры для каждого запроса **не нужно** (экономия ресурсов)

## 3. Implementation Details

### 3.1. Структура файла `ai_core/agents/summarizer.py`

```python
"""
Summarizer Agent

Агент для генерации саммари истории чата используя Google ADK.
"""

from typing import List
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ai_core.common.config import settings
from ai_core.common.models import Message
from ai_core.common.logging import logger

# Создаём session service (один раз на уровне модуля)
_session_service = InMemorySessionService()

# Создаём агента (один раз на уровне модуля)
_summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=settings.GEMINI_MODEL_SMART,
    description="Генерирует краткое саммари истории чата",
    instruction="""You are a helpful assistant. Summarize the following conversation concisely 
in the same language as the conversation. Highlight key decisions and action items.
Provide a well-structured summary in markdown format.""",
)

# Создаём runner (один раз на уровне модуля)
_summarizer_runner = Runner(
    agent=_summarizer_agent,
    app_name="mesh_mind",
    session_service=_session_service,
)


def summarize(messages: List[Message]) -> str:
    """
    Генерирует краткое саммари по списку сообщений.
    
    Args:
        messages: Список объектов Message для суммаризации
        
    Returns:
        Строка с markdown-форматированным саммари
        
    Raises:
        ValueError: Если список сообщений пустой
        Exception: При ошибках вызова API
    """
    if not messages:
        raise ValueError("Список сообщений не может быть пустым")
    
    logger.info(f"Начинаю суммаризацию {len(messages)} сообщений")
    
    # Преобразуем сообщения в текстовый формат
    conversation_text = "\n".join([
        f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {msg.author_name}: {msg.content}"
        for msg in messages
    ])
    
    # Формируем сообщение для агента
    user_message = f"Please summarize this conversation:\n\n{conversation_text}"
    
    logger.debug(f"Промпт для суммаризации: {user_message[:200]}...")
    
    # Вызываем агента через runner
    try:
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )
        
        # Используем sync вызов (или async в зависимости от архитектуры)
        response_text = None
        for event in _summarizer_runner.run(
            user_id="system",  # Для summarizer user_id не критичен
            session_id=f"summary_{hash(conversation_text)}",  # Уникальная сессия
            new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
        
        if not response_text:
            raise Exception("Агент не вернул ответ")
        
        logger.info(f"Саммари успешно сгенерировано, длина: {len(response_text)} символов")
        return response_text
        
    except Exception as e:
        logger.error(f"Ошибка при генерации саммари: {e}")
        raise
```

### 3.2. ADK Dependencies

Необходимые пакеты (добавить в `requirements.txt`):
```
google-adk>=0.1.0
```

### 3.3. Resilience

-   **Retry логика:** ADK имеет встроенную обработку ошибок
-   **Опционально:** Можно добавить декоратор `@retry` из `tenacity` для дополнительной надёжности
-   Для MVP встроенной логики достаточно (YAGNI)

## 4. Verification & Definition of Done

-   [ ] Agent создаётся без ошибок при старте приложения
-   [ ] Agent принимает список из 10 тестовых сообщений
-   [ ] Agent возвращает непустую строку
-   [ ] Саммари точно отражает содержание сообщений (ручная проверка)
-   [ ] **Manual Test:** Запустить `python -m ai_core.agents.summarizer` с тестовыми данными и проверить вывод
-   [ ] Нет ошибок при пустом списке сообщений (должен быть `ValueError`)

## 5. Дополнительные ресурсы

-   [ADK Documentation](https://google.github.io/adk-docs/)
-   [LLM Agents Guide](https://google.github.io/adk-docs/agents/llm-agents/)
-   [ADK Python Repository](https://github.com/google/adk-python)
