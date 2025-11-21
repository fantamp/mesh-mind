from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ai_core.api.dependencies import get_db_session, get_vector_db
from ai_core.api.models import SummarizeRequest, SummarizeResponse, AskRequest, AskResponse
from ai_core.storage.db import get_chat_state, get_messages, update_chat_state
from ai_core.rag.vector_db import VectorDB

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
        
    # 3. Mock Summarizer Agent
    # In real implementation: agent.run(messages)
    msg_texts = [m.content for m in messages]
    summary_text = f"[MOCK SUMMARY] Summary of {len(messages)} messages: " + " ".join(msg_texts[:3]) + "..."
    
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
    # 1. Mock QA Agent / RAG
    # Search Vector Store
    results = vector_db.search(request.query, n_results=3)
    
    # Extract sources
    sources = []
    if results and results.get('documents'):
        for i, doc_list in enumerate(results['documents']):
            for j, doc in enumerate(doc_list):
                meta = results['metadatas'][i][j]
                source_info = f"{meta.get('source', 'unknown')} ({meta.get('type', 'unknown')})"
                sources.append(source_info)
    
    # Generate Answer (Mock)
    answer = f"[MOCK ANSWER] Based on your query '{request.query}', here is some information found in the knowledge base."
    
    return AskResponse(answer=answer, sources=sources)
