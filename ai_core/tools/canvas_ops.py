from typing import Optional, List, Dict, Any
import uuid
from ai_core.tools.utils import run_async
from ai_core.services.canvas_service import canvas_service

def get_current_canvas_info(chat_id: str) -> str:
    """
    Returns information about the current canvas for the chat.
    """
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        return f"Canvas ID: {canvas.id}\nName: {canvas.name or 'Unnamed'}"
    return run_async(_do())

def set_canvas_name(chat_id: str, name: str) -> str:
    """
    Sets the name of the current canvas.
    """
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        updated = await canvas_service.update_canvas(canvas.id, name)
        return f"Canvas renamed to: {updated.name}"
    return run_async(_do())

def create_canvas_frame(chat_id: str, name: str, parent_frame_id: Optional[str] = None) -> str:
    """
    Creates a new frame in the current canvas.
    """
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        parent_uuid = uuid.UUID(parent_frame_id) if parent_frame_id else None
        frame = await canvas_service.create_frame(canvas.id, name, parent_id=parent_uuid)
        return f"Frame created: {frame.name} (ID: {frame.id})"
    return run_async(_do())

def set_frame_name(frame_id: str, name: str) -> str:
    """
    Renames a frame.
    """
    async def _do():
        frame_uuid = uuid.UUID(frame_id)
        updated = await canvas_service.update_frame(frame_uuid, name)
        if updated:
            return f"Frame renamed to: {updated.name}"
        return "Frame not found."
    return run_async(_do())

def list_canvas_frames(chat_id: str) -> str:
    """
    Lists all frames in the current canvas.
    """
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        frames = await canvas_service.get_frames(canvas.id)
        if not frames:
            return "No frames found."
        
        lines = []
        for f in frames:
            parent_info = f" (Parent: {f.parent_id})" if f.parent_id else ""
            lines.append(f"- {f.name} [ID: {f.id}]{parent_info}")
        return "\n".join(lines)
    return run_async(_do())

def add_element_to_frame(element_id: str, frame_id: str) -> str:
    """
    Adds an element to a specific frame (an element can be in multiple frames).
    """
    async def _do():
        el_uuid = uuid.UUID(element_id)
        fr_uuid = uuid.UUID(frame_id)
        success = await canvas_service.add_element_to_frame(el_uuid, fr_uuid)
        if success:
            return f"Element added to frame {frame_id}"
        return "Failed to add element to frame (maybe already there)."
    return run_async(_do())

def remove_element_from_frame(element_id: str, frame_id: str) -> str:
    """
    Removes an element from a specific frame.
    """
    async def _do():
        el_uuid = uuid.UUID(element_id)
        fr_uuid = uuid.UUID(frame_id)
        success = await canvas_service.remove_element_from_frame(el_uuid, fr_uuid)
        if success:
            return f"Element removed from frame {frame_id}"
        return "Failed to remove element from frame (maybe not there)."
    return run_async(_do())

def set_element_name(element_id: str, name: str) -> str:
    """
    Sets a short human-readable name for an element.
    """
    async def _do():
        el_uuid = uuid.UUID(element_id)
        updated = await canvas_service.update_element(el_uuid, name=name)
        if updated:
            return f"Element named: {updated.name}"
        return "Element not found."
    return run_async(_do())
