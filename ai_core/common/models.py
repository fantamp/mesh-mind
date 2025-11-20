from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON
import uuid

class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    source: str  # e.g., "telegram", "email"
    author_id: str
    author_name: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    media_path: Optional[str] = None
    media_type: Optional[str] = None # voice, document

class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    content: str
    doc_metadata: Dict[str, Any] = Field(default={}, sa_type=JSON)
