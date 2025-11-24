import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from ai_core.tools.knowledge_base import search_knowledge_base, fetch_documents
from ai_core.storage.db import Message



@pytest.fixture
def mock_vector_store():
    with patch('ai_core.tools.knowledge_base._vector_store') as mock:
        yield mock



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


