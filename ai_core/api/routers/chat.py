from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ai_core.api.dependencies import get_db_session, get_vector_db
from ai_core.api.models import SummarizeRequest, SummarizeResponse, AskRequest, AskResponse
from ai_core.storage.db import get_chat_state, get_messages, update_chat_state
from ai_core.rag.vector_db import VectorDB
from ai_core.agents.summarizer import summarize as agent_summarize
from ai_core.agents.qa import ask_question as agent_ask
from ai_core.common.models import Message as CommonMessage

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    chat_id = str(request.chat_id)
    
    # 1. Get Chat State
    state = await get_chat_state(chat_id)
    last_msg_id = state.last_summary_message_id if state else None
    
    # 2. Fetch Messages
    # MVP: Just fetch last N messages for now as get_messages logic for "after ID" is not fully implemented in db.py yet
    # Ideally we would filter where id > last_msg_id or created_at > last_summary_time
    messages = await get_messages(chat_id, limit=request.limit)
    
    if not messages:
        return SummarizeResponse(summary="No new messages to summarize.")
        
    # 3. Real Summarizer Agent
    try:
        from loguru import logger
        logger.info(f"Calling agent_summarize for {len(messages)} messages")
        
        # Convert DB messages to Common messages
        common_messages = [
            CommonMessage(
                id=msg.id,
                source=msg.source,
                author_id=msg.chat_id, # Using chat_id as author_id for now
                author_name=msg.author_name,
                content=msg.content,
                timestamp=msg.created_at,
                media_path=msg.media_path,
                media_type=msg.media_type
            ) for msg in messages
        ]
        
        summary_text = agent_summarize(common_messages)
        logger.info("agent_summarize completed successfully")
    except Exception as e:
        logger.error(f"agent_summarize failed: {e}")
        summary_text = f"Error generating summary: {e}"
    
    # 4. Update State
    # We take the ID of the most recent message (first in list because get_messages orders by desc)
    new_last_msg_id = messages[0].id
    await update_chat_state(chat_id, new_last_msg_id)
    
    return SummarizeResponse(summary=summary_text)

@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    vector_db: VectorDB = Depends(get_vector_db)
):
    # 1. Real QA Agent
    try:
        # We use a fixed user_id for now or derive from request if available
        # For MVP, we can use "telegram_user"
        answer = agent_ask(request.query, user_id="telegram_user")
        sources = ["Sources are cited in the answer."]
    except Exception as e:
        answer = f"Error generating answer: {e}"
        sources = []
    
    return AskResponse(answer=answer, sources=sources)
