import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from ai_core.tools.messages import fetch_chat_messages
from ai_core.tools.knowledge_base import search_knowledge_base, fetch_documents
from ai_core.storage.db import Message

@pytest.fixture
def mock_run_async():
    with patch('ai_core.tools.messages.run_async') as mock:
        yield mock

@pytest.fixture
def mock_get_messages():
    with patch('ai_core.tools.messages.get_messages') as mock:
        yield mock

@pytest.fixture
def mock_vector_store():
    with patch('ai_core.tools.knowledge_base._vector_store') as mock:
        yield mock

def test_fetch_chat_messages_success(mock_run_async):
    # Setup mock return
    mock_msg1 = MagicMock(spec=Message)
    mock_msg1.author_name = "Alice"
    mock_msg1.content = "Hello"
    mock_msg1.created_at = datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc)
    
    mock_msg2 = MagicMock(spec=Message)
    mock_msg2.author_name = "Bob"
    mock_msg2.content = "Hi"
    mock_msg2.created_at = datetime(2023, 1, 1, 10, 1, tzinfo=timezone.utc)
    
    # run_async returns the result of the coroutine directly (not a coroutine)
    mock_run_async.return_value = [mock_msg2, mock_msg1] # Newest first usually
    
    result = fetch_chat_messages(chat_id="123")
    
    # Verify run_async was called with the coroutine
    mock_run_async.assert_called_once()
    
    assert "[2023-01-01 10:00] Alice: Hello" in result
    assert "[2023-01-01 10:01] Bob: Hi" in result
    # Check order: oldest first in output
    assert result.index("Alice") < result.index("Bob")

def test_fetch_chat_messages_empty(mock_run_async):
    mock_run_async.return_value = []
    result = fetch_chat_messages(chat_id="123")
    assert "No messages found" in result

def test_search_knowledge_base_success(mock_vector_store):
    mock_vector_store.search.return_value = {
        'documents': [['Doc 1']],
        'metadatas': [[{'source': 'wiki'}]]
    }
    
    result = search_knowledge_base("query", "chat_id")
    assert "Doc 1" in result
    assert "(source: wiki)" in result

def test_fetch_documents_success(mock_vector_store):
    mock_vector_store.get_documents.return_value = [
        {"content": "Doc A", "metadata": {"filename": "a.txt"}},
        {"content": "Doc B", "metadata": {"filename": "b.txt"}}
    ]
    
    result = fetch_documents("chat_id", tags="tag1")
    
    assert len(result) == 2
    assert result[0].content == "Doc A"
    assert result[1].content == "Doc B"
    assert result[0].filename == "a.txt"

def test_fetch_chat_messages_with_since(mock_run_async):
    """Test fetching messages with since filter."""
    # Setup mock return
    mock_msg1 = MagicMock(spec=Message)
    mock_msg1.author_name = "Alice"
    mock_msg1.content = "Old message"
    mock_msg1.created_at = datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc)
    
    mock_msg2 = MagicMock(spec=Message)
    mock_msg2.author_name = "Bob"
    mock_msg2.content = "New message"
    mock_msg2.created_at = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    
    # Mock run_async to return messages when called
    # Note: The tool logic calls get_messages(..., since=...)
    # We need to verify that get_messages was called with the correct since parameter
    # But since we mock run_async which wraps get_messages, we can't easily check get_messages arguments 
    # unless we mock get_messages separately.
    # However, the tool just passes the result of get_messages.
    # So we should mock get_messages to verify the call arguments.
    
    with patch('ai_core.tools.messages.get_messages') as mock_get_messages_inner:
        mock_run_async.return_value = [mock_msg2] # Simulate DB returning filtered messages
        
        since_str = "2023-01-01T11:00:00+00:00"
        result = fetch_chat_messages(chat_id="123", since=since_str)
        
        # Verify get_messages was called with correct since parameter
        # fetch_chat_messages calls run_async(get_messages(...))
        # So we check if get_messages was called
        mock_get_messages_inner.assert_called_once()
        call_kwargs = mock_get_messages_inner.call_args.kwargs
        assert "since" in call_kwargs
        assert call_kwargs["since"] == datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc)
        
        assert "New message" in result
