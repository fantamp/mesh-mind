import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.api.main import app
from ai_core.api.dependencies import get_vector_db, MockVectorDB
from ai_core.storage.db import init_db, engine
from sqlmodel import SQLModel
from unittest.mock import patch, AsyncMock, MagicMock

# Override dependency to ensure we use MockVectorDB during tests if not already
app.dependency_overrides[get_vector_db] = lambda: MockVectorDB()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_read_main(client):
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mesh Mind AI Core API is running"}

def test_ingest_text(client):
    response = client.post(
        "/api/ingest",
        data={
            "text": "Hello world, this is a test message.",
            "metadata": '{"source": "test", "author_name": "tester", "chat_id": "123"}'
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "id" in response.json()

def test_ask(client):
    response = client.post(
        "/api/ask",
        json={"query": "What is this?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()

def test_summarize(client):
    # Mock all DB and service calls to isolate the API test
    with patch("ai_core.api.routers.chat.get_chat_state", new_callable=AsyncMock) as mock_get_state, \
         patch("ai_core.api.routers.chat.get_messages", new_callable=AsyncMock) as mock_get_messages, \
         patch("ai_core.storage.db.get_messages_after_id", new_callable=AsyncMock) as mock_get_messages_after_id, \
         patch("ai_core.api.routers.chat.update_chat_state", new_callable=AsyncMock) as mock_update_state, \
         patch("ai_core.api.routers.chat.run_summarizer") as mock_run_summarizer:
        
        # Setup mocks
        mock_get_state.return_value = None # No previous state
        mock_msg = MagicMock()
        mock_msg.id = "msg1"
        mock_msg.content = "Hello"
        mock_msg.author_name = "User"
        mock_msg.created_at = "2023-01-01"
        mock_get_messages.return_value = [mock_msg]
        mock_run_summarizer.return_value = "Summary text"
        
        response = client.post(
            "/api/summarize",
            json={"chat_id": "123", "limit": 5}
        )
        
        assert response.status_code == 200
        assert response.json() == {"summary": "Summary text"}
