import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ai_core.api.dependencies import get_db_session, get_vector_db
from ai_core.api.models import IngestResponse
from ai_core.storage.db import save_message, Message, save_document_metadata, DocumentMetadata
from ai_core.storage.fs import save_file
from ai_core.rag.vector_db import VectorDB
from ai_core.common.transcription import TranscriptionService

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    metadata: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
    vector_db: VectorDB = Depends(get_vector_db)
):
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in metadata")

    source = meta.get("source", "unknown")
    author_id = meta.get("author_id")
    author_nick = meta.get("author_nick")
    author_name = meta.get("author_name")
    chat_id = meta.get("chat_id", "unknown")

    saved_id = None
    
    # Logic 1: Audio File
    if file and file.content_type and file.content_type.startswith("audio/"):
        content = await file.read()
        file_path = save_file(content, file.filename, "voice")
        
        # Real Transcription
        try:
            transcription_service = TranscriptionService()
            transcription = await transcription_service.transcribe(file_path)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            transcription = f"[TRANSCRIPTION FAILED] Audio file {file.filename} processed but transcription failed."
        
        text = transcription # Update text with transcription
        
        # Save Message
        msg = Message(
            source=source,
            chat_id=chat_id,
            author_id=author_id,
            author_nick=author_nick,
            author_name=author_name,
            content=text,
            media_path=file_path,
            media_type="voice"
        )
        saved_msg = await save_message(msg)
        saved_id = saved_msg.id
        
        # Add to Vector Store
        vector_db.add_texts(
            texts=[text],
            metadatas=[{
                "source": source,
                "chat_id": chat_id,
                "author": author_name,
                "author_id": author_id,
                "author_nick": author_nick,
                "type": "voice",
                "file_path": file_path
            }],
            ids=[saved_id]
        )

    # Logic 2: Document File
    elif file:
        content = await file.read()
        file_path = save_file(content, file.filename, "doc")
        
        # Mock Document Processing
        # In real scenario, we would extract text from PDF/Docx
        doc_text = f"[MOCK DOC CONTENT] Content of {file.filename}"
        text = doc_text
        
        # Save Document Metadata
        doc_meta = DocumentMetadata(
            filename=file.filename,
            file_path=file_path
        )
        await save_document_metadata(doc_meta)
        saved_id = doc_meta.id
        
        # Add to Vector Store
        vector_db.add_texts(
            texts=[doc_text],
            metadatas=[{
                "source": source,
                "chat_id": chat_id,
                "author": author_name,
                "author_id": author_id,
                "author_nick": author_nick,
                "type": "doc",
                "file_path": file_path,
                "filename": file.filename
            }],
            ids=[saved_id]
        )

    # Logic 3: Text Message
    elif text:
        msg = Message(
            source=source,
            chat_id=chat_id,
            author_id=author_id,
            author_nick=author_nick,
            author_name=author_name,
            content=text,
            media_type="text"
        )
        saved_msg = await save_message(msg)
        saved_id = saved_msg.id
        
        # Add to Vector Store
        vector_db.add_texts(
            texts=[text],
            metadatas=[{
                "source": source,
                "chat_id": chat_id,
                "author": author_name,
                "author_id": author_id,
                "author_nick": author_nick,
                "type": "text"
            }],
            ids=[saved_id]
        )
    else:
        raise HTTPException(status_code=400, detail="No file or text provided")

    return IngestResponse(status="ok", id=saved_id, text=text)
