import os
from typing import Tuple, Optional, Dict, Any

# Configuration
TELEGRAM_ALLOWED_CHAT_IDS = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in TELEGRAM_ALLOWED_CHAT_IDS.split(",") if cid.strip()]

def is_chat_allowed(chat_id: int) -> bool:
    """Check if the chat ID is allowed."""
    if not ALLOWED_CHAT_IDS:
        return True # Allow all if whitelist is empty
    return chat_id in ALLOWED_CHAT_IDS

def is_forwarded(message) -> bool:
    return bool(
        getattr(message, "forward_origin", None)
        or getattr(message, "forward_from", None)
        or getattr(message, "forward_sender_name", None)
        or getattr(message, "forward_from_chat", None)
    )

def extract_author_from_message(message) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Возвращает (author_id, author_nick, author_name) исходного автора.
    Для форвардов берём оригинального автора, иначе текущего.
    """
    # Newer Telegram API: forward_origin (may contain sender_user, sender_chat, sender_user_name, chat)
    forward_origin = getattr(message, "forward_origin", None)
    if forward_origin:
        # 1. MessageOriginUser
        origin_user = getattr(forward_origin, "sender_user", None)
        if origin_user:
            author_id = str(origin_user.id) if getattr(origin_user, "id", None) else None
            author_nick = origin_user.username
            fname = origin_user.first_name or ""
            lname = origin_user.last_name or ""
            author_name = f"{fname} {lname}".strip() or None
            return author_id, author_nick, author_name
            
        # 2. MessageOriginChat (Groups)
        origin_chat = getattr(forward_origin, "sender_chat", None)
        if origin_chat:
            return (
                str(origin_chat.id) if getattr(origin_chat, "id", None) else None,
                origin_chat.username,
                origin_chat.title
            )
            
        # 3. MessageOriginChannel (Channels) - uses 'chat' attribute
        origin_channel_chat = getattr(forward_origin, "chat", None)
        if origin_channel_chat:
             return (
                str(origin_channel_chat.id) if getattr(origin_channel_chat, "id", None) else None,
                origin_channel_chat.username,
                origin_channel_chat.title
            )

        # 4. MessageOriginHiddenUser - uses 'sender_user_name'
        origin_hidden_name = getattr(forward_origin, "sender_user_name", None)
        if origin_hidden_name:
            return None, None, origin_hidden_name
            
        # Fallback for older sender_name if still used or other types
        origin_name = getattr(forward_origin, "sender_name", None)
        if origin_name:
            return None, None, origin_name

    # Forwarded from user
    fwd_user = getattr(message, "forward_from", None)
    if fwd_user:
        author_id = str(fwd_user.id) if getattr(fwd_user, "id", None) else None
        author_nick = fwd_user.username
        fname = fwd_user.first_name or ""
        lname = fwd_user.last_name or ""
        author_name = f"{fname} {lname}".strip() or None
        return author_id, author_nick, author_name

    # Forwarded from hidden sender name
    fwd_sender_name = getattr(message, "forward_sender_name", None)
    if fwd_sender_name:
        return None, None, fwd_sender_name

    # Forwarded from chat (channels)
    fwd_chat = getattr(message, "forward_from_chat", None)
    if fwd_chat:
        return str(fwd_chat.id) if getattr(fwd_chat, "id", None) else None, fwd_chat.username, fwd_chat.title

    # Not forwarded — use current sender
    user = getattr(message, "from_user", None) or getattr(message, "chat", None)
    if user:
        author_id = str(user.id) if getattr(user, "id", None) else None
        author_nick = getattr(user, "username", None)
        fname = getattr(user, "first_name", "") or ""
        lname = getattr(user, "last_name", "") or ""
        author_name = f"{fname} {lname}".strip() or None
        return author_id, author_nick, author_name

    return None, None, None


