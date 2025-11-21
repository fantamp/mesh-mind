import sys
import os

# sys.path hack removed

from ai_core.common import settings, setup_logging, Message, Document
from loguru import logger

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
    msg = Message(
        source="telegram",
        author_id="123",
        author_name="Test User",
        content="Hello World"
    )
    print(f"   Message created: {msg}")
    assert msg.id is not None
    assert msg.timestamp is not None
    
    doc = Document(
        filename="test.txt",
        content="Test content",
        doc_metadata={"author": "me", "tags": ["test"]}
    )
    print(f"   Document created: {doc}")
    assert doc.doc_metadata["author"] == "me"
    
    print("\n--- Verification Successful ---")

# Main block removed
