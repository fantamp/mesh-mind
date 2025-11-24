import pytest
from unittest.mock import patch, MagicMock
from ai_core.rag.vector_db import VectorDB
from ai_core.services.agent_service import run_qa as ask_question
from ai_core.services.agent_service import run_document_summarizer as summarize_documents
import re

# Mock implementation of run_agent_sync that simulates agent behavior
# by directly querying the VectorDB. This avoids API calls and 429 errors.
def mock_run_agent_sync(agent, user_message, user_id=None, session_id=None, app_name=None):
    # Extract chat_id from the message
    chat_id_match = re.search(r"chat_id='([^']*)'", user_message)
    chat_id = chat_id_match.group(1) if chat_id_match else None
    
    vector_db = VectorDB()
    
    if "summarize the documents" in user_message:
        # Simulate summarizer: fetch all docs for chat_id
        # Since VectorDB doesn't have "get all", we search with a generic query
        results = vector_db.search("secret code", n_results=10, chat_id=chat_id)
        if results and results.get('documents') and results['documents'][0]:
            return f"Summary based on: {', '.join(results['documents'][0])}"
        return "No documents found."
        
    else:
        # Simulate QA: search for the question
        question_match = re.search(r"Question: (.*)", user_message)
        question = question_match.group(1) if question_match else "query"
        
        results = vector_db.search(question, n_results=1, chat_id=chat_id)
        if results and results.get('documents') and results['documents'][0]:
            return f"Answer based on {results['documents'][0][0]}"
        return "I don't know."

@pytest.mark.asyncio
async def test_context_isolation():
    vector_db = VectorDB()
    
    chat_id_a = "test_chat_A"
    chat_id_b = "test_chat_B"
    
    # Clean up previous runs
    vector_db.delete(where={"chat_id": chat_id_a})
    vector_db.delete(where={"chat_id": chat_id_b})
    
    # Ingest data for Chat A
    texts_a = ["The secret code for Chat A is ALPHA."]
    vector_db.add_texts(texts_a, chat_id=chat_id_a)
    
    # Ingest data for Chat B
    texts_b = ["The secret code for Chat B is BETA."]
    vector_db.add_texts(texts_b, chat_id=chat_id_b)
    
    # Patch run_agent_sync in the service module
    with patch('ai_core.services.agent_service.run_agent_sync', side_effect=mock_run_agent_sync):
        
        # Test QA Agent for Chat A
        # Should find ALPHA, should NOT find BETA
        answer_a = ask_question("What is the secret code?", user_id="tester_A", chat_id=chat_id_a)
        print(f"Answer A: {answer_a}")
        assert "ALPHA" in answer_a
        assert "BETA" not in answer_a
        
        # Test QA Agent for Chat B
        # Should find BETA, should NOT find ALPHA
        answer_b = ask_question("What is the secret code?", user_id="tester_B", chat_id=chat_id_b)
        print(f"Answer B: {answer_b}")
        assert "BETA" in answer_b
        assert "ALPHA" not in answer_b
        
        # Test Summarizer for Chat A
        summary_a = summarize_documents(chat_id=chat_id_a)
        print(f"Summary A: {summary_a}")
        assert "ALPHA" in summary_a
        assert "BETA" not in summary_a
        
        # Test Summarizer for Chat B
        summary_b = summarize_documents(chat_id=chat_id_b)
        print(f"Summary B: {summary_b}")
        assert "BETA" in summary_b
        assert "ALPHA" not in summary_b
    
    # Cleanup
    vector_db.delete(where={"chat_id": chat_id_a})
    vector_db.delete(where={"chat_id": chat_id_b})
