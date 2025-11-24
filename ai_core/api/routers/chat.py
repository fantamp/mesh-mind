from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ai_core.api.dependencies import get_db_session, get_vector_db
from ai_core.api.models import SummarizeRequest, SummarizeResponse, AskRequest, AskResponse
from ai_core.storage.db import get_chat_state, get_messages, update_chat_state
from ai_core.rag.vector_db import VectorDB
from ai_core.services.agent_service import run_qa as agent_ask, run_document_summarizer, run_summarizer
from ai_core.tools.knowledge_base import fetch_documents
from ai_core.common.models import DomainMessage

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    chat_id = str(request.chat_id)
    
    if request.scope == "documents":
        # Summarize documents
        try:
            documents = fetch_documents(chat_id=chat_id, tags=request.tags)
            summary_text = run_document_summarizer(chat_id=chat_id, documents=documents)
        except Exception as e:
            summary_text = f"Error generating document summary: {e}"
        return SummarizeResponse(summary=summary_text)

    # Default: Summarize messages
    # 1. Get Chat State
    state = await get_chat_state(chat_id)
    last_msg_id = state.last_summary_message_id if state else None
    
    # 2. Fetch Messages с учетом фильтрации по времени
    since_dt = None
    if request.since_datetime:
        # Парсинг ISO формата даты-времени
        from datetime import datetime
        try:
            since_dt = datetime.fromisoformat(request.since_datetime.replace('Z', '+00:00'))
        except ValueError:
            # Если формат некорректный, игнорируем
            pass
    
    messages = await get_messages(chat_id, limit=request.limit, since=since_dt)
    
    if not messages:
        return SummarizeResponse(summary="No new messages to summarize.")
        
    # 3. Real Summarizer Agent
    try:
        from loguru import logger
        logger.info(f"Calling run_summarizer for chat_id={chat_id}")
        
        summary_text = run_summarizer(chat_id=chat_id, messages=messages, user_id="api_user")
        logger.info("run_summarizer completed successfully")
    except Exception as e:
        logger.error(f"run_summarizer failed: {e}")
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
        # For MVP, we can use "telegram_user" or chat_id if provided
        user_id = request.chat_id if request.chat_id else "telegram_user"
        answer = agent_ask(request.query, user_id=user_id, chat_id=request.chat_id)
        sources = ["Sources are cited in the answer."]
    except Exception as e:
        # Возвращаем чистое сообщение об ошибке, чтобы пользователь видел красивое сообщение о квоте
        answer = str(e)
        sources = []
    
    return AskResponse(answer=answer, sources=sources)
