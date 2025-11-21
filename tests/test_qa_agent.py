import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_core.agents.qa import search_knowledge_base, ask_question, _vector_store, _qa_runner, _session_service

@pytest.fixture
def mock_vector_store():
    with patch('ai_core.agents.qa._vector_store') as mock:
        yield mock

@pytest.fixture
def mock_runner():
    with patch('ai_core.agents.qa._qa_runner') as mock:
        yield mock

@pytest.fixture
def mock_session_service():
    with patch('ai_core.agents.qa._session_service') as mock:
        yield mock

def test_search_knowledge_base_found(mock_vector_store):
    # Setup mock return value
    mock_vector_store.search.return_value = {
        'documents': [['Chunk 1 content', 'Chunk 2 content']],
        'metadatas': [[{'source': 'doc1.pdf'}, {'source': 'doc2.txt'}]]
    }
    
    result = search_knowledge_base("test query")
    
    assert "Chunk 1 content" in result
    assert "(источник: doc1.pdf)" in result
    assert "Chunk 2 content" in result
    assert "(источник: doc2.txt)" in result
    mock_vector_store.search.assert_called_once_with("test query", n_results=5)

def test_search_knowledge_base_not_found(mock_vector_store):
    mock_vector_store.search.return_value = {'documents': [[]], 'metadatas': [[]]}
    
    result = search_knowledge_base("unknown query")
    
    assert "В базе знаний не найдено релевантной информации" in result

def test_search_knowledge_base_error(mock_vector_store):
    mock_vector_store.search.side_effect = Exception("DB Error")
    
    result = search_knowledge_base("error query")
    
    assert "Ошибка поиска: DB Error" in result

@patch('ai_core.agents.qa.asyncio.run')
def test_ask_question_success(mock_asyncio_run, mock_runner, mock_session_service):
    # Setup mock runner event
    mock_event = MagicMock()
    mock_event.is_final_response.return_value = True
    mock_event.content.parts = [MagicMock(text="Answer from agent")]
    
    mock_runner.run.return_value = [mock_event]
    
    response = ask_question("What is X?", user_id="test_user")
    
    assert response == "Answer from agent"
    # Verify session creation was attempted
    assert mock_asyncio_run.called

def test_ask_question_empty():
    with pytest.raises(ValueError, match="Вопрос не может быть пустым"):
        ask_question("")

@patch('ai_core.agents.qa.asyncio.run')
def test_ask_question_no_response(mock_asyncio_run, mock_runner):
    # Runner returns no events or no final response
    mock_runner.run.return_value = []
    
    with pytest.raises(Exception, match="Агент не вернул ответ"):
        ask_question("Query", user_id="user")

