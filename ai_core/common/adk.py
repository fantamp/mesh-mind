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
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable

from ai_core.common.config import settings
from ai_core.common.logging import logger

# Ensure API key is set
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Global session service
_session_service = InMemorySessionService()

def get_session_service() -> InMemorySessionService:
    """Returns the shared session service instance."""
    return _session_service

# Standard retry decorator for agent operations
# Uses the more robust policy from summarizer (5 attempts)
standard_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=20),
    retry=retry_if_exception_type((
        ResourceExhausted, 
        InternalServerError, 
        ServiceUnavailable,
        Exception 
    )),
    reraise=True
)

def run_agent_sync(
    agent: LlmAgent,
    user_message: str,
    user_id: str = "default_user",
    session_id: Optional[str] = None,
    app_name: str = "agents"
) -> str:
    """
    Executes an ADK agent synchronously, handling asyncio loop complexity.
    
    Args:
        agent: The LlmAgent instance to run.
        user_message: The text message to send to the agent.
        user_id: User identifier for the session.
        session_id: Optional session ID. If None, a new UUID is generated.
        app_name: App name for the session.
        
    Returns:
        The text response from the agent.
        
    Raises:
        Exception: If the agent fails to return a response or other errors occur.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
        
    logger.debug(f"Running agent {agent.name} for user {user_id} (session {session_id})")

    # Create runner
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=_session_service,
    )

    # 1. Create Session (Async handling)
    def create_session_task():
        asyncio.run(_session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        ))

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            logger.debug("Event loop running, using ThreadPoolExecutor for session creation")
            with ThreadPoolExecutor() as executor:
                executor.submit(create_session_task).result()
        else:
            logger.debug("No event loop, running session creation directly")
            create_session_task()
            
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
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
            session_id=session_id,
            new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
                
        if not response_text:
            raise Exception("Agent did not return a final text response")
            
        return response_text
        
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        raise
