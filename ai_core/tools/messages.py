from typing import List, Optional
from ai_core.storage.db import get_messages
from ai_core.tools.utils import run_async

def fetch_chat_messages(chat_id: str, limit: int = 50) -> str:
    """
    Fetches the most recent messages from a specific chat history.
    
    Args:
        chat_id: The ID of the chat to fetch messages from.
        limit: The maximum number of messages to retrieve (default: 50).
        
    Returns:
        A string containing the formatted messages, or a message indicating no history found.
    """
    try:
        messages = run_async(get_messages(chat_id=chat_id, limit=limit))
        
        if not messages:
            return "No messages found for this chat."
            
        # Format messages
        formatted_messages = []
        for msg in messages:
            # Assuming msg has author_name, content, timestamp
            timestamp_str = msg.created_at.strftime('%Y-%m-%d %H:%M') if msg.created_at else "Unknown time"
            formatted_messages.append(f"[{timestamp_str}] {msg.author_name}: {msg.content}")
            
        # Join with newlines (reverse order to show chronological if get_messages returns desc)
        # get_messages returns desc (newest first), so we reverse to have oldest first for reading
        return "\n".join(reversed(formatted_messages))
        
    except Exception as e:
        return f"Error fetching messages: {str(e)}"
