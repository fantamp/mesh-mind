from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON
import uuid

from sqlalchemy import Index

class Message(SQLModel, table=True):
    """
    Unified Message model for both domain logic and database persistence.
    """
    __tablename__ = "messages"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    source: str = Field(index=True) # e.g., "telegram", "email"
    chat_id: str = Field(index=True)
    author_id: Optional[str] = Field(default=None, index=True)
    author_nick: Optional[str] = Field(default=None, index=True)
    author_name: Optional[str] = None
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    media_path: Optional[str] = None
    media_type: Optional[str] = None # voice, document

    __table_args__ = (
        Index("idx_messages_chat_author", "chat_id", "author_id"),
        Index("idx_messages_chat_nick", "chat_id", "author_nick"),
        Index("idx_messages_chat_created", "chat_id", "created_at"),
    )

class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    content: str
    doc_metadata: Dict[str, Any] = Field(default={}, sa_type=JSON)
