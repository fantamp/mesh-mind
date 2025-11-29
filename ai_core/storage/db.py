from typing import Optional, List
from datetime import datetime, timezone
import uuid
from sqlmodel import Field, SQLModel, select
from sqlalchemy import Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ai_core.common.config import settings

# Database Connection
# Ensure the directory exists is handled by fs or manual check, but here we just define the engine.
# We need to convert the path to an async sqlite url.
# Assuming settings.DB_PATH is a relative path like "data/db/mesh_mind.db"
import os

# Ensure DB directory exists
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{settings.DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Models

from ai_core.common.models import Message



# Functions

async def init_db():
    """Creates tables if they don't exist."""
    async with engine.begin() as conn:
        # Для тестов/разработки: создаем таблицы если нет (MVP)
        # await conn.run_sync(SQLModel.metadata.drop_all) # REMOVED: Data safety
        await conn.run_sync(SQLModel.metadata.create_all)

async def save_message(msg: Message) -> Message:
    async with async_session() as session:
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg

async def get_messages(
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    since: Optional[datetime] = None,
    author_id: Optional[str] = None,
    author_nick: Optional[str] = None,
    contains: Optional[str] = None
) -> List[Message]:
    """
    Получить сообщения из чата.
    
    Args:
        chat_id: ID чата
        limit: Максимальное количество сообщений
        offset: Смещение для пагинации
        since: Опциональное время - вернуть только сообщения после этого времени
        author_id: фильтр по id автора
        author_nick: фильтр по никнейму
        contains: подстрока для поиска в тексте сообщения
    """
    async with async_session() as session:
        statement = select(Message).where(Message.chat_id == chat_id)
        
        # Добавить фильтр по времени, если указан
        if since:
            statement = statement.where(Message.created_at >= since)
        
        if author_id:
            statement = statement.where(Message.author_id == author_id)

        if author_nick:
            statement = statement.where(Message.author_nick == author_nick)

        if contains:
            # SQLite LIKE is case-insensitive by default for ASCII; acceptable for MVP
            like_pattern = f"%{contains}%"
            statement = statement.where(Message.content.like(like_pattern))
        
        statement = statement.order_by(Message.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()




