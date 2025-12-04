from typing import Optional, List, Dict, Any
import uuid
from google.adk.tools import ToolContext
from ai_core.tools.utils import run_async, log_tool_call, extract_chat_id
from ai_core.services.canvas_service import canvas_service
from ai_core.common.models import CanvasFrame, CanvasElement, Canvas

async def _ensure_chat_boundaries(chat_id: Optional[str] = None, element_id: Optional[str] = None, frame_id: Optional[str] = None, frame: Optional[CanvasFrame] = None, element: Optional[CanvasElement] = None, canvas: Optional[Canvas] = None):
    if chat_id:
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
    if not canvas:
        raise ValueError("No canvas found for chat")
    if element_id:
        element = await canvas_service.get_element(uuid.UUID(element_id))
    if frame_id:
        frame = await canvas_service.get_frame(uuid.UUID(frame_id))
    if frame:
        if frame.canvas_id != canvas.id:
            raise ValueError(f"Frame {frame.id} does not belong to canvas {canvas.id}")
    if element:
        if element.canvas_id != canvas.id:
            raise ValueError(f"Element {element.id} does not belong to canvas {canvas.id}")

@log_tool_call
def get_current_canvas_info(tool_context: ToolContext) -> str:
    """
    Returns information about the current canvas for the chat.
    """
    chat_id = extract_chat_id(tool_context)
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        return f"Canvas ID: {canvas.id}\nName: {canvas.name or 'Unnamed'}"
    return run_async(_do())

@log_tool_call
def set_canvas_name(tool_context: ToolContext, name: str) -> str:
    """
    Sets the name of the current canvas.
    """
    chat_id = extract_chat_id(tool_context)
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        updated = await canvas_service.update_canvas(canvas.id, name)
        return f"Canvas renamed to: {updated.name}"
    return run_async(_do())

@log_tool_call
def create_canvas_frame(tool_context: ToolContext, name: str, parent_frame_id: Optional[str] = None) -> str:
    """
    Creates a new frame in the current canvas.
    """    
    chat_id = extract_chat_id(tool_context)
    
    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        parent_uuid = uuid.UUID(parent_frame_id) if parent_frame_id else None
        frame = await canvas_service.create_frame(canvas.id, name, parent_id=parent_uuid)
        return f"Frame created: {frame.name} (ID: {frame.id})"
    return run_async(_do())

@log_tool_call
def set_frame_name(frame_id: str, name: str, tool_context: ToolContext) -> str:
    """
    Renames a frame.
    """
    chat_id = extract_chat_id(tool_context)
    
    async def _do():
        frame_uuid = uuid.UUID(frame_id)

        frame = await canvas_service.get_frame(frame_uuid)
        if not frame:
            return "Frame not found."
        await _ensure_chat_boundaries(chat_id, frame=frame)

        updated = await canvas_service.update_frame(frame_uuid, name)
        if updated:
            return f"Frame renamed to: {updated.name}"
        return "Frame not found."
    return run_async(_do())

@log_tool_call
def list_canvas_frames(tool_context: ToolContext) -> str:
    """
    Lists all frames in the current canvas.
    """

    chat_id = extract_chat_id(tool_context)
    
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

@log_tool_call
def add_element_to_frame(element_id: str, frame_id: str, tool_context: ToolContext) -> str:
    """
    Adds an element to a specific frame (an element can be in multiple frames).
    """
    chat_id = extract_chat_id(tool_context)
    
    async def _do():
        el_uuid = uuid.UUID(element_id)
        fr_uuid = uuid.UUID(frame_id)
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)

        element = await canvas_service.get_element(el_uuid)
        if not element:
            return "Element not found."
        
        frame = await canvas_service.get_frame(fr_uuid)
        if not frame:
            return "Frame not found."

        await _ensure_chat_boundaries(canvas=canvas, element=element, frame=frame)

        success = await canvas_service.add_element_to_frame(el_uuid, fr_uuid)
        if success:
            return f"Element added to frame {frame_id}"
        return "Failed to add element to frame (maybe already there)."
    return run_async(_do())

@log_tool_call
def remove_element_from_frame(element_id: str, frame_id: str, tool_context: ToolContext) -> str:
    """
    Removes an element from a specific frame.
    """
    chat_id = extract_chat_id(tool_context)
    async def _do():
        await _ensure_chat_boundaries(chat_id, element_id=element_id, frame_id=frame_id)
        el_uuid = uuid.UUID(element_id)
        fr_uuid = uuid.UUID(frame_id)
        success = await canvas_service.remove_element_from_frame(el_uuid, fr_uuid)
        if success:
            return f"Element removed from frame {frame_id}"
        return "Failed to remove element from frame (maybe not there)."
    return run_async(_do())

@log_tool_call
def set_element_name(element_id: str, name: str, tool_context: ToolContext) -> str:
    """
    Sets a short human-readable name for an element.
    """
    chat_id = extract_chat_id(tool_context)
    async def _do():
        await _ensure_chat_boundaries(chat_id, element_id=element_id)
        el_uuid = uuid.UUID(element_id)
        updated = await canvas_service.update_element(el_uuid, name=name)
        if updated:
            return f"Element named: {updated.name}"
        return "Element not found."
    return run_async(_do())


@log_tool_call
def create_element(
    content: str,
    created_by: str,
    tool_context: ToolContext,
    type: str = "note",
    attributes: Optional[Dict[str, Any]] = None,
    frame_id: Optional[str] = None,
) -> str:
    """
    Creates a new element on the canvas.
    
    Args:
        content: The content of the element (cannot be empty).
        created_by: Short, meaningful name and some ID of the creator (e.g. "canvas_manager", "user:123").
        type: The type of the element (default: "note").
        attributes: Optional dictionary of attributes.
        frame_id: Optional ID of the frame to add the element to.
    """
    chat_id = extract_chat_id(tool_context)
    if not content or not content.strip():
        return "Error: content cannot be empty."

    async def _do():
        canvas = await canvas_service.get_or_create_canvas_for_chat(str(chat_id))
        
        if frame_id:
            await _ensure_chat_boundaries(canvas=canvas, frame_id=frame_id)

        frame_uuid = uuid.UUID(frame_id) if frame_id else None
        
        element = await canvas_service.add_element(
            canvas_id=canvas.id,
            type=type,
            content=content,
            created_by=created_by,
            attributes=attributes,
            frame_id=frame_uuid
        )
        
        return f"Element created: {element.id} (Type: {element.type})"
    return run_async(_do())

@log_tool_call
def edit_element(
    element_id: str,
    tool_context: ToolContext,
    name: Optional[str] = None,
    content: Optional[str] = None,
    type: Optional[str] = None,
    attributes_to_set: Optional[Dict[str, Any]] = None,
    attributes_to_remove: Optional[List[str]] = None,
) -> str:
    """
    Edits an existing element on the canvas.
    
    Args:
        element_id: The ID of the element to edit.
        name: New name for the element.
        content: New content for the element.
        type: New type for the element.
        attributes_to_set: Dictionary of attributes to set or update.
        attributes_to_remove: List of attribute keys to remove.
    """
    chat_id = extract_chat_id(tool_context)
    
    async def _do():
        # Validate ownership
        await _ensure_chat_boundaries(chat_id, element_id=element_id)
        
        el_uuid = uuid.UUID(element_id)
        
        updated = await canvas_service.update_element(
            element_id=el_uuid,
            name=name,
            content=content,
            type=type,
            attributes=attributes_to_set,
            attributes_to_remove=attributes_to_remove
        )
        
        if updated:
            return f"Element updated: {updated.id}"
        return "Element not found."
    return run_async(_do())
