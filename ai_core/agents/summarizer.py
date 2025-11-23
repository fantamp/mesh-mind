"""
Summarizer Agent

Агент для генерации саммари истории чата используя Google ADK.
"""

import asyncio
import os
import uuid
from typing import List

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
# Импортируем исключение ADK для retry


from ai_core.common.config import settings
from ai_core.common.models import DomainMessage
from ai_core.common.logging import logger

# Устанавливаем API key в переменные окружения для ADK
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

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
    app_name="agents",  # Используем "agents" чтобы соответствовать структуре ADK
    session_service=_session_service,
)


@retry(
    stop=stop_after_attempt(5), # Увеличиваем количество попыток
    wait=wait_exponential(multiplier=2, min=4, max=20), # Увеличиваем задержку
    # Ловим как стандартные исключения, так и специфичные для ADK
    retry=retry_if_exception_type((
        ResourceExhausted, 
        InternalServerError, 
        ServiceUnavailable,

        Exception # ADK может оборачивать ошибки, поэтому ловим Exception и проверяем сообщение если нужно, но пока доверимся типам
    )),
    reraise=True
)
def summarize(messages: List[DomainMessage]) -> str:
    """
    Генерирует краткое саммари по списку сообщений.
    
    Args:
        messages: Список объектов DomainMessage для суммаризации
        
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
    
    # Генерируем уникальный session_id
    session_id = str(uuid.uuid4())
    user_id = "system"

    try:
        from concurrent.futures import ThreadPoolExecutor
        
        # Явно создаем сессию асинхронно перед использованием runner'а
        # Если мы уже в event loop (например, в тестах), запускаем в отдельном потоке
        def run_in_thread():
            asyncio.run(_session_service.create_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
            ))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            logger.debug("Running session creation in thread pool")
            with ThreadPoolExecutor() as executor:
                executor.submit(run_in_thread).result()
        else:
            logger.debug("Running session creation directly")
            run_in_thread()
        
        logger.debug(f"Session {session_id} created. Preparing user content.")

        user_content = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )
        
        response_text = None
        logger.debug("Calling runner.run()...")
        # Вызываем runner.run() - это синхронный метод, который внутри запускает event loop
        for event in _summarizer_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            logger.debug(f"Received event: {type(event)}")
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
        
        if not response_text:
            raise Exception("Агент не вернул ответ")
        
        logger.info(f"Саммари успешно сгенерировано, длина: {len(response_text)} символов")
        return response_text
        
    except Exception as e:
        logger.error(f"Ошибка при генерации саммари ({type(e).__name__}): {e}")
        print(f"DEBUG ERROR in summarizer: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


from ai_core.rag.vector_db import VectorDB

# Initialize Vector Store
_vector_store = VectorDB()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        ResourceExhausted, InternalServerError, ServiceUnavailable, Exception
    )),
    reraise=True
)
def summarize_documents(chat_id: str, tags: List[str] = None, limit: int = 20) -> str:
    """
    Summarizes documents from the knowledge base for a specific chat.
    
    Args:
        chat_id: The chat ID to filter documents by.
        tags: Optional list of tags to filter by.
        limit: Maximum number of documents to retrieve.
        
    Returns:
        Markdown formatted summary of the documents.
    """
    logger.info(f"Summarizing documents for chat_id={chat_id}, tags={tags}")
    
    where = None
    if tags:
        if len(tags) == 1:
            where = {"tags": {"$contains": tags[0]}}
        else:
            # ChromaDB doesn't support $contains for multiple values easily in one go without $or or $and
            # For MVP, let's just take the first tag or use $or
            # Or we can iterate. Let's try to filter by the first tag for now or use $or
            where = {"$or": [{"tags": {"$contains": tag}} for tag in tags]}

    try:
        documents = _vector_store.get_documents(limit=limit, where=where, chat_id=chat_id)
        
        if not documents:
            return "No documents found to summarize."
            
        # Combine documents
        combined_text = "\n\n---\n\n".join(documents)
        
        # Prepare prompt
        user_message = f"Please summarize the following documents:\n\n{combined_text}"
        
        # Use the same logic as summarize() but with different content
        # We can reuse the runner and agent
        
        session_id = str(uuid.uuid4())
        user_id = f"summarizer_{chat_id}"

        # Create session
        from concurrent.futures import ThreadPoolExecutor
        
        def run_in_thread():
            try:
                asyncio.run(_session_service.create_session(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id
                ))
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            with ThreadPoolExecutor() as executor:
                executor.submit(run_in_thread).result()
        else:
            run_in_thread()
            
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )
        
        response_text = None
        for event in _summarizer_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
        
        if not response_text:
            raise Exception("Agent did not return a response")
            
        return response_text

    except Exception as e:
        logger.error(f"Error summarizing documents: {e}")
        raise
