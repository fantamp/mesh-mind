from typing import Optional
from datetime import datetime
from ai_core.tools.utils import run_async
from ai_core.storage.db import get_messages

def fetch_messages(
    chat_id: str,
    limit: int = 50,
    since: Optional[str] = None,
    author_id: Optional[str] = None,
    author_nick: Optional[str] = None,
    contains: Optional[str] = None
) -> str:
    """
    Fetches messages from the chat history based on criteria.
    
    Args:
        chat_id: The ID of the chat.
        limit: Max number of messages to return.
        since: ISO datetime string to filter messages after this time.
        author_id: Filter by author id.
        author_nick: Filter by author nickname.
        contains: Substring search in content.
        
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
        messages = run_async(
            get_messages(
                chat_id=chat_id,
                limit=limit,
                since=since_dt,
                author_id=author_id,
                author_nick=author_nick,
                contains=contains
            )
        )
    except Exception as e:
        return f"Error fetching messages: {str(e)}"

    if not messages:
        return "No messages found."

    # Sort ascending by created_at for observer/summarizer readability
    messages_sorted = sorted(messages, key=lambda m: m.created_at)

    from ai_core.common.formatters import format_message_to_string

    formatted_messages = []
    for msg in messages_sorted:
        formatted_messages.append(format_message_to_string(msg))

    return "\n\n\n".join(formatted_messages)
