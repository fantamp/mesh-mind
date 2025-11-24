"""
Unit-тесты для Summarizer Agent
"""

import pytest
from unittest.mock import MagicMock, patch
from ai_core.services.agent_service import run_summarizer as summarize_chat

@pytest.fixture
def mock_run_agent_sync():
    with patch('ai_core.services.agent_service.run_agent_sync') as mock:
        yield mock

def test_summarize_chat_success(mock_run_agent_sync):
    mock_run_agent_sync.return_value = "Summary text"
    
    messages = [MagicMock(author_name="User", content="Hello", timestamp=MagicMock(strftime=lambda x: "2023-01-01"))]
    result = summarize_chat(chat_id="123", messages=messages, instruction="Make it short")
    
    assert result == "Summary text"
    
    mock_run_agent_sync.assert_called_once()
    call_args = mock_run_agent_sync.call_args
    assert "chat_id='123'" in call_args.kwargs['user_message']
    assert "Make it short" in call_args.kwargs['user_message']
    assert "User: Hello" in call_args.kwargs['user_message']

@patch("ai_core.services.agent_service.run_agent_sync")
def test_run_summarizer_with_messages(mock_run_agent_sync):
    """Test run_summarizer with messages."""
    from ai_core.services.agent_service import run_summarizer
    chat_id = "test_chat_limit"
    messages = [MagicMock(author_name="User", content="Hello", timestamp=MagicMock(strftime=lambda x: "2023-01-01"))]
    
    run_summarizer(chat_id=chat_id, messages=messages)
    
    # Verify agent was called with messages in prompt
    mock_run_agent_sync.assert_called_once()
    call_kwargs = mock_run_agent_sync.call_args.kwargs
    user_message = call_kwargs["user_message"]
    
    assert "User: Hello" in user_message
