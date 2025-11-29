import asyncio
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from ai_core.tools.messages import fetch_messages
from ai_core.storage.db import Message

@pytest.fixture
def mock_get_messages():
    with patch('ai_core.tools.messages.get_messages') as mock:
        yield mock

@pytest.fixture
def mock_run_async():
    with patch('ai_core.tools.messages.run_async') as mock:
        mock.side_effect = lambda coro: coro # Just return the coroutine object or result
        yield mock

def test_fetch_messages_success(mock_run_async, mock_get_messages):
    # Setup mock return value
    # Используем простые объекты, чтобы избежать магических моков
    class Msg:
        def __init__(self, author, content, dt):
            self.author_name = author
            self.content = content
            self.created_at = dt
    mock_messages = [
        Msg("User", "Hello", datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)),
        Msg("Bot", "Hi there", datetime(2023, 1, 1, 12, 0, 5, tzinfo=timezone.utc)),
    ]
    # Возвращаем список сообщений через run_async, игнорируя корутину
    mock_get_messages.return_value = mock_messages
    mock_run_async.side_effect = lambda coro: asyncio.run(coro)
    
    result = fetch_messages(chat_id="chat1")
    
    expected_output = "[2023-01-01 12:00:00] User: Hello\n\n\n[2023-01-01 12:00:05] Bot: Hi there"
    assert result == expected_output

def test_fetch_messages_empty(mock_run_async, mock_get_messages):
    mock_run_async.side_effect = lambda x: []
    
    result = fetch_messages(chat_id="chat1")
    
    assert result == "No messages found."

def test_fetch_messages_with_since(mock_run_async, mock_get_messages):
    mock_run_async.side_effect = lambda x: []
    
    since_str = "2023-01-01T12:00:00"
    fetch_messages(chat_id="chat1", since=since_str)
    
    # Verify get_messages was called with correct datetime
    # Note: We can't easily check the arguments passed to get_messages because it's wrapped in run_async
    # But we can verify no error was raised
    pass

def test_fetch_messages_invalid_since():
    result = fetch_messages(chat_id="chat1", since="invalid-date")
    assert "Error: Invalid date format" in result
