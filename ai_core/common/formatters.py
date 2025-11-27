from typing import Any
from datetime import datetime

def format_message_to_string(msg: Any) -> str:
    """
    Formats a message object (DomainMessage or DB Message) into a string for display.
    Format: [YYYY-MM-DD HH:MM:SS] Name (@nick): Content
    """
    # Handle different field names for timestamp (created_at vs timestamp)
    dt = getattr(msg, 'created_at', None) or getattr(msg, 'timestamp', None)
    if dt:
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp = "Unknown time"

    # Extract author info
    name = getattr(msg, "author_name", None) or ""
    nick_val = getattr(msg, "author_nick", None)
    nick = nick_val.strip() if isinstance(nick_val, str) and nick_val.strip() else None
    aid_val = getattr(msg, "author_id", None)
    aid = str(aid_val) if isinstance(aid_val, (str, int)) and str(aid_val).strip() else None

    if nick:
        # If name is present, show "Name (@nick)", else just "@nick"
        base = name.strip() if name else ""
        who = f"{base} (@{nick})".strip() if base else f"@{nick}"
    elif aid:
        # If no nick, show "Name (id=...)" or "id=..."
        base = name.strip() if name else ""
        if base:
            who = f"{base} (id={aid})"
        else:
            who = f"id={aid}"
    else:
        who = name or "unknown"

    return f"[{timestamp}] {who}: {msg.content}"
