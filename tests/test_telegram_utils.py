import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update
from telegram.error import BadRequest
from telegram_bot.utils import send_safe_message

@pytest.mark.asyncio
async def test_send_safe_message():
    print("Testing send_safe_message...")
    
    # Mock Update and Message
    mock_update = MagicMock(spec=Update)
    mock_message = AsyncMock()
    mock_message.message_id = 12345
    mock_update.message = mock_message
    
    # Test 1: Normal short message
    print("Test 1: Normal short message")
    mock_message.reset_mock()
    await send_safe_message(mock_update, "Hello World")
    mock_message.reply_text.assert_called_with("Hello World", parse_mode="Markdown", reply_to_message_id=12345)
    print("PASS")
    
    # Test 2: Long message truncation
    print("Test 2: Long message truncation")
    mock_message.reset_mock()
    long_text = "a" * 5000
    await send_safe_message(mock_update, long_text)
    args, kwargs = mock_message.reply_text.call_args
    sent_text = args[0]
    assert len(sent_text) <= 4096
    assert "(Response truncated due to length limit)" in sent_text
    assert kwargs["parse_mode"] == "Markdown"
    assert kwargs["reply_to_message_id"] == 12345
    print("PASS")
    
    # Test 3: Fallback on BadRequest
    print("Test 3: Fallback on BadRequest")
    mock_message.reset_mock()
    # Setup mock to raise BadRequest on first call, then succeed
    mock_message.reply_text.side_effect = [BadRequest("Can't parse entities"), None]
    
    await send_safe_message(mock_update, "Bad_Markdown_Text")
    
    # Check calls
    assert mock_message.reply_text.call_count == 2
    # First call with markdown
    args1, kwargs1 = mock_message.reply_text.call_args_list[0]
    assert args1[0] == "Bad_Markdown_Text"
    assert kwargs1["parse_mode"] == "Markdown"
    assert kwargs1["reply_to_message_id"] == 12345
    
    # Second call without markdown (fallback)
    args2, kwargs2 = mock_message.reply_text.call_args_list[1]
    assert args2[0] == "Bad_Markdown_Text"
    assert "parse_mode" not in kwargs2 or kwargs2["parse_mode"] is None
    assert kwargs2["reply_to_message_id"] == 12345
    print("PASS")

if __name__ == "__main__":
    asyncio.run(test_send_safe_message())
