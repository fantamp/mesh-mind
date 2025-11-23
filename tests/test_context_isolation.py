import pytest
import asyncio
from ai_core.rag.vector_db import VectorDB
from ai_core.agents.qa import ask_question
from ai_core.agents.summarizer import summarize_documents

# Use a separate collection for testing to avoid messing with real data
# But VectorDB uses a hardcoded collection name "mesh_mind_v1"
# For MVP, we can just use unique chat_ids that won't collide with real usage

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
    
    # Test QA Agent for Chat A
    # Should find ALPHA, should NOT find BETA
    answer_a = ask_question("What is the secret code?", user_id="tester", chat_id=chat_id_a)
    print(f"Answer A: {answer_a}")
    assert "ALPHA" in answer_a
    assert "BETA" not in answer_a
    
    # Test QA Agent for Chat B
    # Should find BETA, should NOT find ALPHA
    answer_b = ask_question("What is the secret code?", user_id="tester", chat_id=chat_id_b)
    print(f"Answer B: {answer_b}")
    assert "BETA" in answer_b
    assert "ALPHA" not in answer_b
    
    # Test Summarizer for Chat A
    summary_a = summarize_documents(chat_id=chat_id_a)
    print(f"Summary A: {summary_a}")
    assert "ALPHA" in summary_a or "Chat A" in summary_a or "code" in summary_a
    assert "BETA" not in summary_a
    
    # Test Summarizer for Chat B
    summary_b = summarize_documents(chat_id=chat_id_b)
    print(f"Summary B: {summary_b}")
    assert "BETA" in summary_b or "Chat B" in summary_b or "code" in summary_b
    assert "ALPHA" not in summary_b
    
    # Cleanup
    vector_db.delete(where={"chat_id": chat_id_a})
    vector_db.delete(where={"chat_id": chat_id_b})
