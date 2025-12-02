import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
import uuid
from ai_core.common.models import CanvasElement
from ai_core.tools.elements import fetch_elements, _fetch_elements_impl

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
        result = await _fetch_elements_impl(chat_id=123, limit=10)
        assert "Hello" in result
        mock_service.get_elements.assert_called_with(
            canvas_id=mock_canvas.id,
            limit=10,
            since=None,
            frame_id=None
        )

        # Test 2: With frame_id (Valid)
        result = await _fetch_elements_impl(chat_id=123, frame_id=str(frame_uuid))
        assert "Hello" in result
        mock_service.get_elements.assert_called_with(
            canvas_id=mock_canvas.id,
            limit=10,
            since=None,
            frame_id=frame_uuid
        )
        
        # Test 3: With frame_id (Invalid - Not in chat)
        other_frame_uuid = uuid.uuid4()
        result = await _fetch_elements_impl(chat_id=123, frame_id=str(other_frame_uuid))
        assert "Error: Frame not found in this chat" in result
    
def test_fetch_elements_invalid_date():
    result = fetch_elements(chat_id=123, since="invalid-date")
    assert "Error: Invalid date format" in result

def test_fetch_elements_missing_chat_id():
    result = fetch_elements(chat_id=None)
    assert "Error: chat_id is required" in result
