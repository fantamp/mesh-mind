import asyncio
import os
from datetime import datetime, timedelta, timezone
import uuid

from ai_core.storage import init_db, save_file
from ai_core.storage.db import async_session
from ai_core.common.models import CanvasElement
from sqlmodel import select

import pytest

@pytest.mark.asyncio
async def test_storage():
    print("1. Initializing Database...")
    await init_db()
    print("   Database initialized.")
    
    print("\n2. Testing Message Storage (via CanvasElement)...")
    msg = CanvasElement(
        canvas_id=uuid.uuid4(),
        type="message",
        content="Hello, this is a test message.",
        created_by="telegram:123",
        attributes={
            "source": "test_script",
            "chat_id": "test_chat_123",
            "author_name": "Tester"
        }
    )
    
    async with async_session() as session:
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        
    print(f"   Message saved with ID: {msg.id}")
    
    print("\n3. Retrieving Messages...")
    async with async_session() as session:
        # Simulate get_messages logic
        statement = select(CanvasElement).where(CanvasElement.type == "message")
        result = await session.execute(statement)
        messages = result.scalars().all()
        
    assert len(messages) > 0
    # Filter for our message specifically in case DB is reused
    found_msg = next((m for m in messages if m.id == msg.id), None)
    assert found_msg is not None
    assert found_msg.content == "Hello, this is a test message."
    print(f"   Retrieved message verified.")
    
    print("\n4. Testing File Storage...")
    dummy_content = b"This is some dummy content for a file."
    file_path = save_file(dummy_content, "test_file.txt", "doc")
    print(f"   File saved at: {file_path}")
    
    if os.path.exists(file_path):
        print("   File exists on disk.")
        with open(file_path, "rb") as f:
            content = f.read()
            assert content == dummy_content
            print("   File content verified.")
    else:
        print("   ERROR: File not found on disk!")
        return

    print("\nSUCCESS: All storage tests passed!")

@pytest.mark.asyncio
async def test_get_messages_with_since():
    """Тест фильтрации сообщений по времени"""
    await init_db()
    
    chat_id = "test_chat_time_filter"
    now = datetime.now(timezone.utc)
    canvas_id = uuid.uuid4()
    
    # Создать несколько сообщений с разным временем
    old_msg = CanvasElement(
        canvas_id=canvas_id,
        type="message",
        content="Old message",
        created_by="telegram:User1",
        created_at=now - timedelta(hours=2),
        attributes={"chat_id": chat_id}
    )
    recent_msg = CanvasElement(
        canvas_id=canvas_id,
        type="message",
        content="Recent message",
        created_by="telegram:User1",
        created_at=now - timedelta(minutes=10),
        attributes={"chat_id": chat_id}
    )
    
    async with async_session() as session:
        session.add(old_msg)
        session.add(recent_msg)
        await session.commit()
    
    # Получить только сообщения за последний час
    since = now - timedelta(hours=1)
    
    async with async_session() as session:
        statement = select(CanvasElement).where(
            CanvasElement.type == "message",
            CanvasElement.created_at >= since
        )
        # In a real scenario we'd filter by chat_id too, but here we just check time
        result = await session.execute(statement)
        messages = result.scalars().all()
    
    # Должно быть только одно сообщение (recent) из этих двух
    # Note: DB might have other messages, so we check if recent is there and old is not
    msg_ids = [m.id for m in messages]
    assert recent_msg.id in msg_ids
    assert old_msg.id not in msg_ids

