import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_core.services.agent_service import run_qa as ask_question

@pytest.fixture
def mock_run_agent_sync():
    with patch('ai_core.services.agent_service.run_agent_sync') as mock:
        yield mock

def test_ask_question_success(mock_run_agent_sync):
    mock_run_agent_sync.return_value = "Answer from agent"
    
    response = ask_question("What is X?", user_id="test_user", chat_id="123")
    
    assert response == "Answer from agent"
    # Verify run_agent_sync was called with correct arguments
    mock_run_agent_sync.assert_called_once()
    call_args = mock_run_agent_sync.call_args
    assert call_args.kwargs['user_id'] == "test_user"
    assert "What is X?" in call_args.kwargs['user_message']
    assert "chat_id='123'" in call_args.kwargs['user_message']

def test_ask_question_empty():
    with pytest.raises(ValueError, match="Вопрос не может быть пустым"):
        ask_question("")

def test_ask_question_error(mock_run_agent_sync):
    mock_run_agent_sync.side_effect = Exception("Agent error")
    
    with pytest.raises(Exception, match="Agent error"):
        ask_question("Query", user_id="user")
