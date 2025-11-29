import asyncio
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import patch

from ai_core.common.config import settings

# Override DB path for demo
# Since DB_PATH is a property, we need to patch it
demo_db_path = os.path.join(settings.PROJECT_ROOT, "data/db/demo_chat.db")
patcher = patch.object(type(settings), 'DB_PATH', property(lambda self: demo_db_path))
patcher.start()

from ai_core.storage.db import init_db, save_message, get_messages, Message
from ai_core.agents.orchestrator.agent import root_agent as orchestrator
from ai_core.common.adk import run_agent_sync
from ai_core.common.formatters import format_message_to_string

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def setup_demo_data():
    """Initializes the demo database with sample messages."""
    print(f"{Colors.CYAN}📦 Initializing test database ({settings.DB_PATH})...{Colors.ENDC}")
    
    # Remove existing demo db if exists to start fresh
    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)
        
    await init_db()
    
    chat_id = "demo_chat_123"
    now = datetime.now(timezone.utc)
    
    messages_data = [
        ("alice", "Alice", "Всем привет! Кто-нибудь работал с Python 3.12?", 60),
        ("bob", "Bob", "Привет, Алиса! Да, я уже пробовал. Там классные улучшения в f-strings.", 55),
        ("charlie", "Charlie", "Hi guys! Does anyone know how to fix the asyncio error?", 50),
        ("alice", "Alice", "@charlie, скинь трейсбек, посмотрим.", 45),
        ("bob", "Bob", "Кстати, вы видели новый релиз Mesh Mind?", 40),
        ("alice", "Alice", "Да, мульти-агентная система выглядит круто.", 35),
        ("charlie", "Charlie", "I agree. The orchestrator pattern is very powerful.", 30),
        ("alice", "Alice", "Давайте обсудим это на митинге завтра.", 25),
        ("bob", "Bob", "Ок. Во сколько?", 20),
        ("alice", "Alice", "В 10:00 UTC.", 15),
        ("system", "System", "Meeting scheduled for 10:00 UTC.", 10),
        ("bob", "Bob", "Отлично, буду.", 5),
        ("charlie", "Charlie", "I'll be there too.", 2),
    ]
    
    for nick, name, content, minutes_ago in messages_data:
        msg = Message(
            source="demo",
            chat_id=chat_id,
            author_id=f"user_{nick}",
            author_name=name,
            author_nick=nick,
            content=content,
            created_at=now - timedelta(minutes=minutes_ago),
            media_type="text"
        )
        await save_message(msg)
        
    print(f"{Colors.GREEN}   ✓ Created {len(messages_data)} test messages{Colors.ENDC}")
    return chat_id


async def print_demo_chat(chat_id: str):
    """Выводит содержимое демо-чата перед запуском кейсов."""
    print_separator("DEMO CHAT CONTEXT")
    messages = await get_messages(chat_id=chat_id, limit=1000)

    if not messages:
        print(f"{Colors.WARNING}История чата пуста.{Colors.ENDC}")
        return

    # Сортируем по времени для удобства чтения
    for msg in sorted(messages, key=lambda m: m.created_at):
        formatted = format_message_to_string(msg)
        print(f"{Colors.CYAN}{formatted}{Colors.ENDC}")

def print_separator(title=""):
    if title:
        print(f"\n{Colors.HEADER}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
        print(f"{Colors.BOLD}[{title}]{Colors.ENDC}")
        print(f"{Colors.HEADER}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    else:
        print(f"\n{Colors.HEADER}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")

async def run_demo_case(title: str, user_input: str, chat_id: str, expected_agent: str):
    print_separator(title)
    print(f"👤 {Colors.BOLD}USER:{Colors.ENDC} \"{user_input}\"")
    
    start_time = time.time()
    
    # Prepare context as the bot would
    contexted_text = f"Context: chat_id={chat_id}\nUser message in the group Telegram chat:\n\n{user_input}"
    
    try:
        response = await asyncio.to_thread(
            run_agent_sync,
            agent=orchestrator,
            user_message=contexted_text,
            user_id="demo_user",
            session_id=chat_id
        )
        
        duration = time.time() - start_time
        
        print(f"🤖 {Colors.BLUE}ORCHESTRATOR:{Colors.ENDC} Routing logic executed")
        
        if response == "null" or not response:
             print(f"🤫 {Colors.WARNING}RESULT:{Colors.ENDC} (Silent Mode - No Response)")
        else:
             print(f"📊 {Colors.GREEN}RESULT:{Colors.ENDC}\n{response}")
             
        print(f"{Colors.CYAN}⏱️  Completed in {duration:.2f}s{Colors.ENDC}")
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ ERROR: {e}{Colors.ENDC}")

async def main():
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("========================================")
    print("  MESH MIND: Multi-Agent Demo")
    print("========================================")
    print(f"{Colors.ENDC}")
    
    try:
        chat_id = await setup_demo_data()

        await print_demo_chat(chat_id)
        
        # Case 1: Summary
        await run_demo_case(
            "TEST 1: Summary Request",
            "Summarize the last 10 messages",
            chat_id,
            "chat_summarizer"
        )
        
        # Case 2: Search
        await run_demo_case(
            "TEST 2: Search Request",
            "Find messages from alice about Python",
            chat_id,
            "chat_observer"
        )
        
        # Case 3: Silent Mode
        await run_demo_case(
            "TEST 3: Silent Mode (Casual Chat)",
            "Hello everyone, how are you doing today?",
            chat_id,
            "None"
        )
        
        print("\n✨ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n{Colors.FAIL}CRITICAL ERROR: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
