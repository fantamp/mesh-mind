import sys
import os

# sys.path hack removed

from ai_core.common import settings, setup_logging, CanvasElement
from loguru import logger
import uuid

def test_common_lib():
    print("--- Testing Common Library ---")
    
    # 1. Test Settings
    print(f"1. Settings Loaded:")
    print(f"   ENV: {settings.ENV}")
    print(f"   LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"   GOOGLE_API_KEY: {'*' * len(settings.GOOGLE_API_KEY) if settings.GOOGLE_API_KEY else 'MISSING'}")
    
    assert settings.GOOGLE_API_KEY, "API Key is missing"
    if settings.GOOGLE_API_KEY == "dummy_key_for_testing":
        print("WARNING: Using dummy API key")
    
    # 2. Test Logging
    print("\n2. Testing Logging (Check console output below):")
    setup_logging()
    logger.info("This is an INFO message from loguru.")
    logger.debug("This is a DEBUG message.")
    
    # 3. Test Models
    print("\n3. Testing Models:")
    
    # Simulate a Message
    msg = CanvasElement(
        canvas_id=uuid.uuid4(),
        type="message",
        content="Hello World",
        created_by="telegram:123",
        attributes={
            "source": "telegram",
            "chat_id": "test_chat",
            "author_name": "Test User"
        }
    )
    print(f"   Message (CanvasElement) created: {msg}")
    assert msg.id is not None
    assert msg.created_at is not None
    assert msg.type == "message"
    
    # Simulate a Document
    doc = CanvasElement(
        canvas_id=uuid.uuid4(),
        type="file",
        content="Test content",
        created_by="user:me",
        attributes={
            "filename": "test.txt",
            "author": "me", 
            "tags": ["test"]
        }
    )
    print(f"   Document (CanvasElement) created: {doc}")
    assert doc.attributes["author"] == "me"
    
    print("\n--- Verification Successful ---")
