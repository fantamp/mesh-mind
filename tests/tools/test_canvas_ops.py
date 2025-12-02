import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from ai_core.common.models import CanvasElement

@pytest.mark.asyncio
async def test_create_element():
    # Patch canvas_service where it is imported in canvas_ops
    with patch('ai_core.tools.canvas_ops.canvas_service', new_callable=AsyncMock) as mock_service:
        from ai_core.tools.canvas_ops import create_element
        
        # Setup mocks
        mock_canvas = MagicMock()
        mock_canvas.id = uuid.uuid4()
        mock_service.get_or_create_canvas_for_chat.return_value = mock_canvas
        
        mock_element = MagicMock(spec=CanvasElement)
        mock_element.id = uuid.uuid4()
        mock_element.type = "note"
        mock_service.add_element.return_value = mock_element
        
        # Test execution
        result = create_element(
            chat_id=123,
            content="Test note",
            created_by="tester",
            type="note",
            attributes={"color": "yellow"}
        )
        
        # Verify result
        assert f"Element created: {mock_element.id}" in result
        
        # Verify service calls
        mock_service.get_or_create_canvas_for_chat.assert_called_with("123")
        mock_service.add_element.assert_called_once()
        
        call_kwargs = mock_service.add_element.call_args[1]
        assert call_kwargs["canvas_id"] == mock_canvas.id
        assert call_kwargs["content"] == "Test note"
        assert call_kwargs["type"] == "note"
        assert call_kwargs["attributes"] == {"color": "yellow"}
        assert call_kwargs["created_by"] == "tester"

@pytest.mark.asyncio
async def test_create_element_with_frame():
    with patch('ai_core.tools.canvas_ops.canvas_service', new_callable=AsyncMock) as mock_service:
        from ai_core.tools.canvas_ops import create_element
        
        mock_canvas = MagicMock()
        mock_canvas.id = uuid.uuid4()
        mock_service.get_or_create_canvas_for_chat.return_value = mock_canvas
        
        mock_element = MagicMock(spec=CanvasElement)
        mock_element.id = uuid.uuid4()
        mock_element.type = "note"
        mock_service.add_element.return_value = mock_element
        
        frame_id = str(uuid.uuid4())
        
        result = create_element(
            chat_id=123,
            content="Test note in frame",
            created_by="tester",
            frame_id=frame_id
        )
        
        assert f"Element created: {mock_element.id}" in result
        
        call_kwargs = mock_service.add_element.call_args[1]
        assert call_kwargs["frame_id"] == uuid.UUID(frame_id)

@pytest.mark.asyncio
async def test_create_element_validation():
    from ai_core.tools.canvas_ops import create_element
    
    # Test invalid chat_id
    result = create_element(
        chat_id="not_an_int",
        content="content",
        created_by="tester"
    )
    assert "Error: chat_id must be an integer" in result
    
    # Test empty content
    result = create_element(
        chat_id=123,
        content="",
        created_by="tester"
    )
    assert "Error: content cannot be empty" in result
    
    result = create_element(
        chat_id=123,
        content="   ",
        created_by="tester"
    )
    assert "Error: content cannot be empty" in result
