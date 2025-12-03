import uuid
import re
from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from ai_core.tools.utils import run_async, log_tool_call

# Helper for fuzzy time parsing
def _parse_time_range(time_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parses a natural language time string into a (start, end) tuple.
    Returns (None, None) if parsing fails.
    """
    if not time_str:
        return None, None
    
    s = time_str.strip().lower()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if s == 'yesterday':
        # Start of yesterday to start of today
        start = today_start - timedelta(days=1)
        end = today_start
        return start, end
    
    if s == 'today':
        return today_start, None
        
    # "X hours/minutes/days ago"
    match = re.match(r'(\d+)\s+(hour|minute|day)s?\s+ago', s)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit == 'hour':
            return now - timedelta(hours=val), None
        elif unit == 'minute':
            return now - timedelta(minutes=val), None
        elif unit == 'day':
            return now - timedelta(days=val), None

    # "last X hours/minutes/days"
    match = re.match(r'last\s+(\d+)\s+(hour|minute|day)s?', s)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit == 'hour':
            return now - timedelta(hours=val), None
        elif unit == 'minute':
            return now - timedelta(minutes=val), None
        elif unit == 'day':
            return now - timedelta(days=val), None

    # Explicit range "ISO to ISO"
    # Try splitting by " to "
    if ' to ' in s:
        parts = s.split(' to ')
        if len(parts) == 2:
            try:
                start = datetime.fromisoformat(parts[0].strip().replace('Z', '+00:00'))
                end = datetime.fromisoformat(parts[1].strip().replace('Z', '+00:00'))
                # Ensure timezone awareness if naive
                if start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)
                if end.tzinfo is None: end = end.replace(tzinfo=timezone.utc)
                return start, end
            except ValueError:
                pass

    # Try single ISO
    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt, None
    except ValueError:
        pass
        
    return None, None

@log_tool_call
def fetch_elements(
    chat_id: int,
    limit: int = 10,
    time_range: Optional[str] = None,
    created_by: Optional[str] = None,
    author: Optional[str] = None,
    contains: Optional[str] = None,
    include_details: bool = False,
    frame_id: Optional[str] = None
) -> str:
    """
    Fetches elements (messages, notes, etc.) from the canvas history based on criteria.
    
    Returns a JSON string containing a list of element objects.
    
    Args:
        chat_id: The ID of the chat. It must be an integer.
        limit: Max number of elements to return.
        time_range: Filter elements by time. Supports:
               - Natural language: "yesterday" (full day), "today", "last 3 hours", "20 minutes ago".
               - ISO format: "2023-01-01T10:00:00".
               - Range: "2023-01-01T10:00 to 2023-01-01T12:00".
        created_by: Case-insensitive substring match on the element's creator's ID (e.g. "telegram:user:123").
        author: Case-insensitive substring match on content author name or nickname (in attributes).
        contains: Case-insensitive substring search in content.
        include_details: If True, returns all available fields (canvas_id, frame_ids, attributes). 
                         If False (default), returns only id, type, created_at, author, and content.
        frame_id: Optional ID of the frame to filter by. Must belong to the chat's canvas.
        
    Returns:
        A JSON string representing a list of elements.
    """
    return run_async(_fetch_elements_impl(
        chat_id=chat_id,
        limit=limit,
        time_range=time_range,
        created_by=created_by,
        author=author,
        contains=contains,
        include_details=include_details,
        frame_id=frame_id
    ))

async def _fetch_elements_impl(
    chat_id: int,
    limit: int = 10,
    time_range: Optional[str] = None,
    created_by: Optional[str] = None,
    author: Optional[str] = None,
    contains: Optional[str] = None,
    include_details: bool = False,
    frame_id: Optional[str] = None
) -> str:
    if not chat_id or type(chat_id) != int:
        return "Error: chat_id is required. It must be an integer."

    start_dt = None
    end_dt = None
    
    if time_range:
        start_dt, end_dt = _parse_time_range(time_range)
        if not start_dt and not end_dt:
             return f"Error: Invalid format for 'time_range': {time_range}. Use 'yesterday', 'today', 'X hours ago', or ISO format."

    frame_uuid = None
    if frame_id:
        try:
            frame_uuid = uuid.UUID(frame_id)
        except ValueError:
            return f"Error: Invalid frame_id format: {frame_id}"

    try:
        # Resolve canvas for chat
        from ai_core.services.canvas_service import canvas_service
        
        canvas = await canvas_service.get_or_create_canvas_for_chat(str(chat_id))
        
        # Verify frame belongs to canvas if frame_id is provided
        if frame_uuid:
            frames = await canvas_service.get_frames(canvas.id)
            if frame_uuid not in [f.id for f in frames]:
                return "Error: Frame not found in this chat."
        
        # Fetch a larger batch to allow for filtering in Python
        fetch_limit = max(limit * 5, 100)
        
        # Pass start_dt as 'since' to the service for DB-level filtering
        elements = await canvas_service.get_elements(
            canvas_id=canvas.id,
            limit=fetch_limit,
            since=start_dt,
            frame_id=frame_uuid
        )
        
    except Exception as e:
        return f"Error fetching elements: {str(e)}"

    if not elements:
        return "[]" # Return empty JSON list

    # Filter in Python
    filtered_elements = []
    
    for el in elements:
        # Filter: end_time (if specified)
        if end_dt:
            # Ensure timezone awareness for comparison
            el_created = el.created_at
            if el_created.tzinfo is None:
                el_created = el_created.replace(tzinfo=timezone.utc)
            
            if el_created >= end_dt:
                continue
                
        # Filter: created_by (substring, case-insensitive)
        if created_by:
            if created_by.lower() not in el.created_by.lower():
                continue
                
        # Filter: author (substring in attributes.author_name or author_nick)
        if author:
            attrs = el.attributes or {}
            a_name = attrs.get('author_name', '')
            a_nick = attrs.get('author_nick', '')
            
            if author.lower() not in a_name.lower() and author.lower() not in a_nick.lower():
                continue

        # Filter: contains (substring in content, case-insensitive)
        if contains:
            if contains.lower() not in el.content.lower():
                continue
                
        filtered_elements.append(el)

    # Sort ascending by created_at for observer/summarizer readability
    elements_sorted = sorted(filtered_elements, key=lambda m: m.created_at)
    
    # Apply limit after filtering (take last N for most recent)
    if len(elements_sorted) > limit:
        elements_sorted = elements_sorted[-limit:]

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
