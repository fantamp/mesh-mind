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
    
    # run_async returns the result of the coroutine
    mock_run_async.return_value = [mock_msg2, mock_msg1] # Newest first usually
    
    result = fetch_chat_messages(chat_id="123")
    
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
    mock_vector_store.get_documents.return_value = ["Doc A", "Doc B"]
    
    result = fetch_documents("chat_id", tags="tag1")
    
    assert "Doc A" in result
    assert "Doc B" in result
    assert "---" in result
