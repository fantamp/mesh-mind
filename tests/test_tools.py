import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
import uuid
import os
from ai_core.common.models import CanvasElement
from ai_core.tools.elements import fetch_elements, _fetch_elements_impl
from google.adk.tools import ToolContext

def create_mock_tool_context(chat_id: int) -> ToolContext:
    context = MagicMock(spec=ToolContext)
    context.state = {"chat_id": chat_id}
    return context

@pytest.fixture
def mock_run_async():
    # Patch run_async where it is imported in elements.py
    with patch('ai_core.tools.elements.run_async') as mock:
        mock.side_effect = lambda coro: coro # Just return the coroutine object or result
        yield mock

@pytest.mark.asyncio
async def test_fetch_elements_filters():
    # Setup mock data
    class El:
        def __init__(self, created_by, content, dt, type="message"):
            self.id = uuid.uuid4()
            self.created_by = created_by
            self.content = content
            self.created_at = dt
            self.type = type
            self.attributes = {}
            self.canvas_id = uuid.uuid4()
            self.frames = []

    mock_elements = [
        El("telegram:User", "Hello", datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)),
    ]

    # Mock canvas service
    with patch("ai_core.services.canvas_service.canvas_service") as mock_service:
        # Setup mock returns
        mock_canvas = MagicMock()
        mock_canvas.id = uuid.uuid4()
        mock_service.get_or_create_canvas_for_chat = AsyncMock(return_value=mock_canvas)
        mock_service.get_elements = AsyncMock(return_value=mock_elements)
        
        # Setup frames for validation
        frame_uuid = uuid.uuid4()
        mock_frame = MagicMock()
        mock_frame.id = frame_uuid
        mock_service.get_frames = AsyncMock(return_value=[mock_frame])

        # Test 1: Basic call
        tool_context = create_mock_tool_context(123)
        result = await _fetch_elements_impl(tool_context=tool_context, limit=10)
        assert "Hello" in result
        mock_service.get_elements.assert_called_with(
            canvas_id=mock_canvas.id,
            limit=100, # fetch_limit is max(limit * 5, 100)
            since=None,
            frame_id=None
        )

        # Test 2: With frame_id (Valid)
        result = await _fetch_elements_impl(tool_context=tool_context, frame_id=str(frame_uuid))
        assert "Hello" in result
        mock_service.get_elements.assert_called_with(
            canvas_id=mock_canvas.id,
            limit=100,
            since=None,
            frame_id=frame_uuid
        )
        
        # Test 3: With frame_id (Invalid - Not in chat)
        other_frame_uuid = uuid.uuid4()
        result = await _fetch_elements_impl(tool_context=tool_context, frame_id=str(other_frame_uuid))
        assert "Error: Frame not found in this chat" in result
    
def test_fetch_elements_invalid_date():
    tool_context = create_mock_tool_context(123)
    result = fetch_elements(tool_context=tool_context, time_range="invalid-date")
    assert "Error: Invalid format for 'time_range'" in result

def test_fetch_elements_missing_chat_id():
    # If chat_id is missing from context, extract_chat_id should raise ValueError
    # But fetch_elements wraps it in run_async which might propagate the error or handle it.
    # Looking at extract_chat_id, it raises ValueError.
    # fetch_elements calls run_async(_fetch_elements_impl).
    # _fetch_elements_impl calls extract_chat_id first thing.
    # If extract_chat_id raises, the tool call raises.
    # So we should expect an exception.
    
    context = MagicMock(spec=ToolContext)
    context.state = {}
    
    # We need to ensure os.getenv("CHAT_ID") is also empty or mocked.
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Access denied: Chat ID not found"):
             fetch_elements(tool_context=context)
