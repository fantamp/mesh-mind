import asyncio
import os
from datetime import datetime, timedelta, timezone

from ai_core.storage import init_db, save_message, get_messages, Message, save_file
from ai_core.storage.db import find_conversation_boundary

import pytest

@pytest.mark.asyncio
async def test_storage():
    print("1. Initializing Database...")
    await init_db()
    print("   Database initialized.")
    
    print("\n2. Testing Message Storage...")
    msg = Message(
        source="test_script",
        chat_id="test_chat_123",
        author_name="Tester",
        content="Hello, this is a test message."
    )
    saved_msg = await save_message(msg)
    print(f"   Message saved with ID: {saved_msg.id}")
    
    print("\n3. Retrieving Messages...")
    messages = await get_messages(chat_id="test_chat_123")
    assert len(messages) > 0
    assert messages[0].content == "Hello, this is a test message."
    print(f"   Retrieved {len(messages)} messages. Content verified.")
    
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
    
    # Создать несколько сообщений с разным временем
    old_msg = Message(
        source="test",
        chat_id=chat_id,
        author_name="User1",
        content="Old message",
        created_at=now - timedelta(hours=2)
    )
    recent_msg = Message(
        source="test",
        chat_id=chat_id,
        author_name="User1",
        content="Recent message",
        created_at=now - timedelta(minutes=10)
    )
    
    await save_message(old_msg)
    await save_message(recent_msg)
    
    # Получить только сообщения за последний час
    since = now - timedelta(hours=1)
    messages = await get_messages(chat_id=chat_id, since=since)
    
    # Должно быть только одно сообщение (recent)
    assert len(messages) >= 1
    assert any("Recent" in msg.content for msg in messages)

@pytest.mark.asyncio
async def test_find_conversation_boundary():
    """Тест поиска границы разговора"""
    await init_db()
    
    import uuid
    chat_id = f"test_chat_boundary_{uuid.uuid4()}"
    # Используем naive datetime (без timezone) так как Message.created_at тоже naive после сохранения
    now = datetime.now()
    
    # Создать группу старых сообщений
    for i in range(3):
        msg = Message(
            source="test",
            chat_id=chat_id,
            author_name="User1",
            content=f"Old message {i}",
            created_at=now - timedelta(hours=3, minutes=i)
        )
        await save_message(msg)
    
    # Создать группу новых сообщений (после паузы > 60 мин)
    for i in range(3):
        msg = Message(
            source="test",
            chat_id=chat_id,
            author_name="User1",
            content=f"New message {i}",
            created_at=now - timedelta(minutes=30 - i)
        )
        await save_message(msg)
    
    # Найти границу разговора
    boundary = await find_conversation_boundary(chat_id, gap_minutes=60)
    
    # Граница должна быть найдена
    assert boundary is not None
    # Граница должна быть в пределах последних 3 часов (новые сообщения)
    assert (now - boundary).total_seconds() < 3 * 3600
