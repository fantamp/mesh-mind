from typing import Optional
from datetime import datetime
from ai_core.tools.utils import run_async
# from ai_core.storage.db import get_messages # Removed

def fetch_elements(
    chat_id: int,
    limit: int = 10,
    since: Optional[str] = None,
    author_id: Optional[str] = None,
    author_nick: Optional[str] = None,
    contains: Optional[str] = None,
    include_details: bool = False
) -> str:
    """
    Fetches elements (messages, notes, etc.) from the canvas history based on criteria.
    
    Returns a JSON string containing a list of element objects.
    
    Args:
        chat_id: The ID of the chat. It must be an integer.
        limit: Max number of elements to return.
        since: ISO datetime string to filter elements after this time.
        author_id: Filter by author id.
        author_nick: Filter by author nickname.
        contains: Substring search in content.
        include_details: If True, returns all available fields (canvas_id, frame_ids, attributes). 
                         If False (default), returns only id, type, created_at, author, and content.
        
    Returns:
        A JSON string representing a list of elements.
        Example (include_details=False):
        [
            {
                "id": "uuid",
                "type": "message",
                "created_at": "ISO-timestamp",
                "author": "user_id",
                "content": "text"
            }
        ]
        
        Example (include_details=True):
        [
            {
                "id": "uuid",
                "type": "message",
                "created_at": "ISO-timestamp",
                "author": "user_id",
                "content": "text",
                "canvas_id": "uuid",
                "frame_ids": ["uuid"],
                "attributes": {...}
            }
        ]
    """
    if not chat_id or type(chat_id) != int:
        return "Error: chat_id is required. It must be an integer."

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except ValueError:
            return f"Error: Invalid date format for 'since': {since}. Use ISO format (YYYY-MM-DDTHH:MM:SS)."

    try:
        # Resolve canvas for chat
        from ai_core.services.canvas_service import canvas_service
        
        # We need to run async code in sync tool
        async def _fetch():
            canvas = await canvas_service.get_or_create_canvas_for_chat(str(chat_id))
            return await canvas_service.get_elements(
                canvas_id=canvas.id,
                limit=limit,
                since=since_dt,
                # type="message" # Removed type filter to fetch all elements as per name change
            )

        elements = run_async(_fetch())
        
    except Exception as e:
        return f"Error fetching elements: {str(e)}"

    if not elements:
        return "[]" # Return empty JSON list

    # Sort ascending by created_at for observer/summarizer readability
    elements_sorted = sorted(elements, key=lambda m: m.created_at)

    import json

    messages_data = []
    for el in elements_sorted:
        msg_data = {
            "id": str(el.id),
            "type": el.type,
            "created_at": el.created_at.isoformat(),
            "author": el.created_by,
            "content": el.content
        }
        
        if include_details:
            frame_ids = [str(f.id) for f in el.frames]
            msg_data.update({
                "canvas_id": str(el.canvas_id),
                "frame_ids": frame_ids,
                "attributes": el.attributes
            })
            
        messages_data.append(msg_data)

    return json.dumps(messages_data, ensure_ascii=False, indent=2)
