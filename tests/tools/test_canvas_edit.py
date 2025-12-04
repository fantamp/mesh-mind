import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from ai_core.common.models import CanvasElement

@pytest.mark.asyncio
async def test_edit_element():
    with patch('ai_core.tools.canvas_ops.canvas_service', new_callable=AsyncMock) as mock_service:
        from ai_core.tools.canvas_ops import edit_element
        
        # Setup mocks
        mock_canvas = MagicMock()
        mock_canvas.id = uuid.uuid4()
        mock_service.get_or_create_canvas_for_chat.return_value = mock_canvas
        
        mock_element = MagicMock(spec=CanvasElement)
        mock_element.id = uuid.uuid4()
        mock_element.canvas_id = mock_canvas.id # Fix: Match canvas ID
        mock_element.type = "note"
        mock_element.content = "Old content"
        mock_element.attributes = {"color": "blue", "size": "small"}
        
        mock_service.get_element.return_value = mock_element # Ensure get_element returns the mock
        
        # Mock update_element to return the updated element (simulated)
        def update_side_effect(element_id, name=None, content=None, type=None, attributes=None, attributes_to_remove=None):
            if content:
                mock_element.content = content
            if type:
                mock_element.type = type
            if attributes:
                mock_element.attributes.update(attributes)
            if attributes_to_remove:
                for k in attributes_to_remove:
                    mock_element.attributes.pop(k, None)
            return mock_element
            
        mock_service.update_element.side_effect = update_side_effect
        
        # Test 1: Update content and type
        result = edit_element(
            element_id=str(mock_element.id),
            tool_context=MagicMock(), # Mock context
            content="New content",
            type="task"
        )
        
        assert f"Element updated: {mock_element.id}" in result
        assert mock_element.content == "New content"
        assert mock_element.type == "task"
        
        # Test 2: Update attributes (add/set and remove)
        result = edit_element(
            element_id=str(mock_element.id),
            tool_context=MagicMock(),
            attributes_to_set={"color": "red", "priority": "high"},
            attributes_to_remove=["size"]
        )
        
        assert f"Element updated: {mock_element.id}" in result
        assert mock_element.attributes["color"] == "red"
        assert mock_element.attributes["priority"] == "high"
        assert "size" not in mock_element.attributes

@pytest.mark.asyncio
async def test_edit_element_not_found():
    with patch('ai_core.tools.canvas_ops.canvas_service', new_callable=AsyncMock) as mock_service:
        from ai_core.tools.canvas_ops import edit_element
        
        mock_canvas = MagicMock()
        mock_canvas.id = uuid.uuid4()
        mock_service.get_or_create_canvas_for_chat.return_value = mock_canvas
        
        mock_service.update_element.return_value = None
        
        # Mock get_element to return an element that belongs to the canvas, 
        # so we pass the boundary check but fail at update (simulating race condition or other failure)
        # OR we can test the boundary check failure itself.
        # Let's test the update failure first as intended by the original test structure.
        mock_element = MagicMock(spec=CanvasElement)
        mock_element.canvas_id = mock_canvas.id
        mock_service.get_element.return_value = mock_element

        result = edit_element(
            element_id=str(uuid.uuid4()),
            tool_context=MagicMock(),
            content="New content"
        )
        
        assert "Element not found" in result
