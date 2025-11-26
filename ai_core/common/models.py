from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON
import uuid

class DomainMessage(SQLModel, table=True):
    """
    Модель сообщения предметной области (Domain Model).

    Описывает структуру сообщения, используемую в бизнес-логике приложения,
    API-эндпоинтах и пользовательском интерфейсе.

    Используется для:
    - Унификации формата сообщений между различными компонентами (Telegram, UI, API).
    - Передачи данных между агентами и сервисами.
    - Отображения сообщений в UI.

    Отличается от модели хранения (storage.db.Message) тем, что является
    абстракцией уровня приложения, а не уровня базы данных.
    """
    __tablename__ = "message" # Explicit table name to avoid migration issues if possible, or just let it default to domainmessage
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    source: str  # e.g., "telegram", "email"
    author_id: str
    author_name: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    media_path: Optional[str] = None
    media_type: Optional[str] = None # voice, document

class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    content: str
    doc_metadata: Dict[str, Any] = Field(default={}, sa_type=JSON)
