from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from loguru import logger
import os

from ai_core.api.dependencies import get_db_session, get_vector_db
from ai_core.api.models import SummarizeRequest, SummarizeResponse, AskRequest, AskResponse, ChatMessageRequest, ChatMessageResponse
from ai_core.storage.db import get_chat_state, get_messages, update_chat_state, save_message
from ai_core.rag.vector_db import VectorDB
from ai_core.services.agent_service import run_qa as agent_ask, run_document_summarizer, run_summarizer, run_orchestrator
from ai_core.tools.knowledge_base import fetch_documents
from ai_core.common.models import Message
from ai_core.common.config import settings

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
    # Pull Approach: We delegate fetching to the agent.
    # We just pass the instruction (if any) and let the agent handle it.
    
    # Construct instruction based on request params
    instruction_parts = []
    if request.since_datetime:
        instruction_parts.append(f"since {request.since_datetime}")
    if request.limit:
        instruction_parts.append(f"limit {request.limit}")
        
    instruction = " ".join(instruction_parts) if instruction_parts else None
        
    # 3. Real Summarizer Agent
    try:
        from loguru import logger
        logger.info(f"Calling run_summarizer for chat_id={chat_id}")
        
        summary_text = run_summarizer(chat_id=chat_id, instruction=instruction, user_id="api_user")
        logger.info("run_summarizer completed successfully")
    except Exception as e:
        logger.error(f"run_summarizer failed: {e}")
        summary_text = f"Error generating summary: {e}"
    
    # 4. Update State
    # Since we don't fetch messages here, we can't easily update the last_msg_id based on fetched messages.
    # However, the agent might return the last processed message ID in the summary or we might need another way.
    # For MVP with Pull approach, we might skip updating state here or do it differently.
    # Let's just update timestamp for now or skip.
    # To keep it simple and safe, we won't update last_msg_id here as we don't know what the agent read.
    # If state tracking is critical, the agent should return metadata.
    
    return SummarizeResponse(summary=summary_text)

@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    vector_db: VectorDB = Depends(get_vector_db)
):
    # 0. Fast path for missing key
    if not settings.GOOGLE_API_KEY:
        return AskResponse(answer="Mock answer (QA disabled: no API key)", sources=[])

    # 1. Real QA Agent
    try:
        user_id = request.chat_id if request.chat_id else "telegram_user"
        answer = agent_ask(request.query, user_id=user_id, chat_id=request.chat_id)
        sources = ["Sources are cited in the answer."]
    except Exception as e:
        answer = str(e)
        sources = []
    
    return AskResponse(answer=answer, sources=sources)

@router.post("/chat/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db_session),
    vector_db: VectorDB = Depends(get_vector_db),
):
    """
    Gateway endpoint: save message via ingest logic, then call orchestrator.
    """
    # 1. Save message (text only) unless skip_save
    if not request.skip_save:
        try:
            msg = Message(
                source="telegram",
                chat_id=request.chat_id,
                author_id=request.user_id,
                author_nick=request.user_nick,
                author_name=request.user_name,
                content=request.text,
                media_type="text"
            )
            saved = await save_message(msg)
            vector_db.add_texts(
                texts=[request.text],
                metadatas=[{
                    "source": "telegram",
                    "chat_id": request.chat_id,
                    "author": request.user_name,
                    "author_id": request.user_id,
                    "author_nick": request.user_nick,
                    "type": "text"
                }],
                ids=[saved.id]
            )
        except Exception as e:
            logger.error(f"Failed to ingest message: {e}")
            raise HTTPException(status_code=500, detail="Failed to ingest message")

    # 2. Call orchestrator
    try:
        reply = run_orchestrator(
            chat_id=request.chat_id,
            user_id=request.user_id,
            user_message=request.text,
            reply_to=request.reply_to_message_id
        )
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        raise HTTPException(status_code=500, detail="Orchestrator failed")

    return ChatMessageResponse(reply=reply)
