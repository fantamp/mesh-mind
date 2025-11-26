from typing import Optional
from datetime import datetime
from ai_core.tools.utils import run_async
from ai_core.storage.db import get_messages

def fetch_messages(chat_id: str, limit: int = 50, since: Optional[str] = None) -> str:
    """
    Fetches messages from the chat history based on criteria.
    
    Args:
        chat_id: The ID of the chat.
        limit: Max number of messages to return.
        since: ISO datetime string to filter messages after this time.
        
    Returns:
        A string representation of the messages.
    """
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except ValueError:
            return f"Error: Invalid date format for 'since': {since}. Use ISO format (YYYY-MM-DDTHH:MM:SS)."

    try:
        messages = run_async(get_messages(chat_id=chat_id, limit=limit, since=since_dt))
    except Exception as e:
        return f"Error fetching messages: {str(e)}"

    if not messages:
        return "No messages found."

    formatted_messages = []
    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        formatted_messages.append(f"[{timestamp}] {msg.author_name}: {msg.content}")

    return "\n".join(formatted_messages)
