import asyncio
import os
import sys

# Add project root to python path
sys.path.append(os.getcwd())

from ai_core.storage import init_db, save_message, get_messages, Message, save_file

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

if __name__ == "__main__":
    asyncio.run(test_storage())
