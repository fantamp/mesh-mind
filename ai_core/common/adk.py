"""
Common utilities for Google ADK agents.
"""

import asyncio
import os
import uuid
from typing import Optional, Generator, Any
from concurrent.futures import ThreadPoolExecutor

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from google.genai.errors import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable

from ai_core.common.config import settings
from ai_core.common.logging import logger

# Ensure API key is set
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Global session service
db_url = f"sqlite+aiosqlite:///{settings.SESSION_DB_PATH}"
_session_service = DatabaseSessionService(db_url=db_url)

def get_session_service() -> DatabaseSessionService:
    """Returns the shared session service instance."""
    return _session_service

# Standard retry decorator for agent operations
# Uses the more robust policy from summarizer (5 attempts)
# NOTE: ResourceExhausted (429) убран из retry - при исчерпании квоты retry бесполезен
standard_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=20),
    retry=retry_if_exception_type((
        InternalServerError, 
        ServiceUnavailable,
    )),
    reraise=True
)

def run_agent_sync(
    agent: LlmAgent,
    user_message: str,
    chat_id: str,
    user_id: str = "default_user",
    app_name: str = "agents"
) -> str:
    """
    Executes an ADK agent synchronously, handling asyncio loop complexity.
    
    Args:
        agent: The LlmAgent instance to run.
        user_message: The text message to send to the agent.
        user_id: User identifier for the session.
        chat_id: Optional chat ID
        app_name: App name for the session.
        
    Returns:
        The text response from the agent.
        
    Raises:
        Exception: If the agent fails to return a response or other errors occur.
    """
    logger.debug(f"Running agent {agent.name} for user {user_id} (session {chat_id})")

    # Create runner
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=_session_service,
    )

    # 1. Create Session (Async handling)
    # Проверяем, существует ли сессия - если да, переиспользуем её
    def create_session_task():
        # Проверяем существование сессии
        try:
            session = asyncio.run(_session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=chat_id
            ))
            if session:
                logger.debug(f"Reusing existing session_id={chat_id}, state={session.state}")
                return
        except Exception:
            # Сессия не существует, создаём новую
            pass
            
        session = asyncio.run(_session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=chat_id,
            state={
                "chat_id": chat_id
            }
        ))
        logger.debug(f"Created new session_id={chat_id}, state={session.state}")
        

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            logger.debug("Event loop running, using ThreadPoolExecutor for session creation")
            with ThreadPoolExecutor() as executor:
                session = executor.submit(create_session_task).result()
        else:
            logger.debug("No event loop, running session creation directly")
            session = create_session_task()            
    except Exception as e:
        logger.error(f"Failed to handle session: {e}")
        raise

    # 2. Run Agent (Sync Runner.run handles its own loop if needed, but returns generator)
    # Note: Runner.run is synchronous but blocks.
    
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=user_message)]
    )
    
    response_text = None
    
    try:
        for event in runner.run(
            user_id=user_id,
            session_id=chat_id,
            new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
                
        return response_text
        
    except Exception as e:
        # Проверяем цепочку исключений на наличие ClientError (429)
        # ADK может оборачивать ошибки в свои типы (например _ResourceExhaustedError)
        cause = e
        client_error = None
        
        # Ищем ClientError в цепочке причин
        while cause:
            if isinstance(cause, ClientError):
                client_error = cause
                break
            cause = getattr(cause, '__cause__', None) or getattr(cause, '__context__', None)
            
        if client_error and client_error.status_code == 429:
            error_details = client_error.response_json.get('error', {})
            message = error_details.get('message', 'Unknown quota error')
            details = error_details.get('details', [])
            
            # Извлекаем полезную информацию
            quota_info = []
            for detail in details:
                if detail.get('@type') == 'type.googleapis.com/google.rpc.QuotaFailure':
                    for violation in detail.get('violations', []):
                        quota_info.append(
                            f"- Модель: {violation.get('quotaDimensions', {}).get('model', 'unknown')}\n"
                            f"- Квота: {violation.get('quotaMetric', 'unknown')}\n"
                            f"- Лимит: {violation.get('quotaValue', 'unknown')}"
                        )
                elif detail.get('@type') == 'type.googleapis.com/google.rpc.RetryInfo':
                    retry_delay = detail.get('retryDelay', '')
                    quota_info.append(f"- Retry after: {retry_delay}")
            
            quota_details = "\n".join(quota_info) if quota_info else "Нет дополнительных деталей"
            
            error_message = (
                f"❌ Ошибка: квота API исчерпана, попробуйте позже\n\n"
                f"Сообщение API: {message}\n\n"
                f"Технические детали:\n{quota_details}"
            )
            
            logger.warning(f"ResourceExhausted for agent {agent.name}: {error_message}")
            raise Exception(error_message) from client_error
            
        # Игнорируем ошибку закрытого event loop при завершении
        if isinstance(e, RuntimeError) and "Event loop is closed" in str(e):
            logger.debug("Ignored 'Event loop is closed' error during cleanup")
            return response_text if response_text else "Agent finished but loop closed early."

        logger.error(f"Error during agent execution: {e}")
        raise
