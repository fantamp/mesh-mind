import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from ai_core.storage.db import Message

@pytest.mark.asyncio
async def test_fetch_messages_filters():
    # Mocking get_messages directly since fetch_messages calls run_async(get_messages(...))
    # But fetch_messages imports get_messages. We need to patch where it is imported.
    with patch('ai_core.tools.messages.get_messages', new_callable=AsyncMock) as mock_get:
        from ai_core.tools.messages import fetch_messages
        
        # Setup mock return
        mock_msg = MagicMock(spec=Message)
        mock_msg.content = "Test message"
        mock_msg.created_at = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_msg.author_name = "Alice"
        mock_msg.author_nick = "alice"
        mock_msg.author_id = "123"
        
        mock_get.return_value = [mock_msg]
        
        # Test 1: Basic call
        result = fetch_messages(chat_id="chat1")
        assert "Alice (@alice): Test message" in result
        mock_get.assert_called_with(
            chat_id="chat1", limit=50, since=None, author_id=None, author_nick=None, contains=None
        )
        
        # Test 2: With filters
        fetch_messages(
            chat_id="chat1", 
            limit=10, 
            since="2023-01-01T00:00:00Z", 
            author_id="123", 
            contains="hello"
        )
        
        call_args = mock_get.call_args[1]
        assert call_args["limit"] == 10
        assert call_args["author_id"] == "123"
        assert call_args["contains"] == "hello"
        assert call_args["since"] == datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
