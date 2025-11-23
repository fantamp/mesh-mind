"""
Summarizer Agent

Агент для генерации саммари истории чата используя Google ADK.
"""

import uuid
from typing import List

from google.adk.agents import LlmAgent

from ai_core.common.config import settings
from ai_core.common.models import DomainMessage
from ai_core.common.logging import logger
from ai_core.common.adk import run_agent_sync, standard_retry
from ai_core.rag.vector_db import VectorDB

# Создаём агента (один раз на уровне модуля)
_summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=settings.GEMINI_MODEL_SMART,
    description="Генерирует краткое саммари истории чата",
    instruction="""You are a helpful assistant. Summarize the following conversation concisely 
in the same language as the conversation. Highlight key decisions and action items.
Provide a well-structured summary in markdown format.""",
)

@standard_retry
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
    
    # Используем shared helper
    return run_agent_sync(
        agent=_summarizer_agent,
        user_message=user_message,
        user_id="system"
    )


# Initialize Vector Store
_vector_store = VectorDB()

@standard_retry
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
            where = {"$or": [{"tags": {"$contains": tag}} for tag in tags]}

    try:
        documents = _vector_store.get_documents(limit=limit, where=where, chat_id=chat_id)
        
        if not documents:
            return "No documents found to summarize."
            
        # Combine documents
        combined_text = "\n\n---\n\n".join(documents)
        
        # Prepare prompt
        user_message = f"Please summarize the following documents:\n\n{combined_text}"
        
        # Use shared helper
        # Note: user_id is set to ensure unique session per summarization request if needed,
        # but run_agent_sync generates a new session_id by default if not provided.
        # We pass a descriptive user_id for logging.
        return run_agent_sync(
            agent=_summarizer_agent,
            user_message=user_message,
            user_id=f"summarizer_{chat_id}"
        )

    except Exception as e:
        logger.error(f"Error summarizing documents: {e}")
        raise
