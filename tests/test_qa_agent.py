import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_core.agents.qa import search_knowledge_base, ask_question

@pytest.fixture
def mock_vector_store():
    with patch('ai_core.agents.qa._vector_store') as mock:
        yield mock

@pytest.fixture
def mock_run_agent_sync():
    with patch('ai_core.agents.qa.run_agent_sync') as mock:
        yield mock

def test_search_knowledge_base_found(mock_vector_store):
    # Setup mock return value
    mock_vector_store.search.return_value = {
        'documents': [['Chunk 1 content', 'Chunk 2 content']],
        'metadatas': [[{'source': 'doc1.pdf'}, {'source': 'doc2.txt'}]]
    }
    
    result = search_knowledge_base("test query", chat_id="test_chat")
    
    assert "Chunk 1 content" in result
    assert "(источник: doc1.pdf)" in result
    assert "Chunk 2 content" in result
    assert "(источник: doc2.txt)" in result
    mock_vector_store.search.assert_called_once_with("test query", n_results=5, chat_id="test_chat")

def test_search_knowledge_base_not_found(mock_vector_store):
    mock_vector_store.search.return_value = {'documents': [[]], 'metadatas': [[]]}
    
    result = search_knowledge_base("unknown query", chat_id="test_chat")
    
    assert "В базе знаний не найдено релевантной информации" in result

def test_search_knowledge_base_error(mock_vector_store):
    mock_vector_store.search.side_effect = Exception("DB Error")
    
    result = search_knowledge_base("error query", chat_id="test_chat")
    
    assert "Ошибка поиска: DB Error" in result

def test_ask_question_success(mock_run_agent_sync):
    mock_run_agent_sync.return_value = "Answer from agent"
    
    response = ask_question("What is X?", user_id="test_user")
    
    assert response == "Answer from agent"
    # Verify run_agent_sync was called with correct arguments
    mock_run_agent_sync.assert_called_once()
    call_args = mock_run_agent_sync.call_args
    assert call_args.kwargs['user_id'] == "test_user"
    assert "What is X?" in call_args.kwargs['user_message']

def test_ask_question_empty():
    with pytest.raises(ValueError, match="Вопрос не может быть пустым"):
        ask_question("")

def test_ask_question_error(mock_run_agent_sync):
    mock_run_agent_sync.side_effect = Exception("Agent error")
    
    with pytest.raises(Exception, match="Agent error"):
        ask_question("Query", user_id="user")

