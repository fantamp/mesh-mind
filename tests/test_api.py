import pytest
from fastapi.testclient import TestClient
from ai_core.api.main import app
from ai_core.api.dependencies import get_vector_db, MockVectorDB

# Override dependency to ensure we use MockVectorDB during tests if not already
app.dependency_overrides[get_vector_db] = lambda: MockVectorDB()

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mesh Mind AI Core API is running"}

def test_ingest_text():
    response = client.post(
        "/ingest",
        data={
            "text": "Hello world, this is a test message.",
            "metadata": '{"source": "test", "author_name": "tester", "chat_id": "123"}'
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "id" in response.json()

def test_ask():
    response = client.post(
        "/ask",
        json={"query": "What is this?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()

def test_summarize():
    response = client.post(
        "/summarize",
        json={"chat_id": 123, "limit": 5}
    )
    assert response.status_code == 200
    assert "summary" in response.json()
