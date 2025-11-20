# Specification: API Service (ai_core/api)

## 1. Overview
This module implements the REST API using FastAPI. It serves as the gateway for the Telegram Bot, CLI tools, and Admin UI to interact with the AI Core.

## 2. Requirements

### 2.1. Framework
-   **Library:** `fastapi`, `uvicorn`.
-   **Host:** `0.0.0.0` (or `127.0.0.1` for local only).
-   **Port:** `8000` (default).

### 2.2. Endpoints

#### `POST /ingest`
-   **Purpose:** Save a message, document, or audio file.
-   **Input:** `multipart/form-data`
    -   `file`: Optional (for docs/audio).
    -   `text`: Optional (for text messages).
    -   `metadata`: JSON string (source, author, chat_id, etc.).
-   **Logic:**
    1.  If `file` is audio:
        -   Save to `data/media/voice/...`.
        -   Call `TranscriptionService.transcribe`.
        -   Update `text` with transcription.
    2.  If `file` is document:
        -   Save to `data/docs/...`.
        -   Call `IngestionService.process_document`.
    3.  Save to SQLite `messages` (if it's a message).
    4.  Call `VectorStore.add_texts` to save to ChromaDB.
-   **Output:** `{"status": "ok", "id": "..."}`.

#### `POST /summarize`
-   **Purpose:** Generate a summary of recent messages for a specific chat.
-   **Input:** `SummarizeRequest` (chat_id, limit).
-   **Logic:**
    1.  Call `StorageLayer.get_chat_state(chat_id)` to get `last_summary_message_id`.
    2.  Fetch messages from SQLite *after* this ID (or last N if no state).
    3.  Call `SummarizerAgent.run(messages)`.
    4.  Call `StorageLayer.update_chat_state(chat_id, last_message_id)` to mark progress.
-   **Output:** `{"summary": "..."}`.

#### `POST /ask`
-   **Purpose:** Answer a user question using RAG.
-   **Input:** `AskRequest` (query, history).
-   **Logic:**
    1.  Call `QAAgent.run(query)`.
-   **Output:** `{"answer": "...", "sources": [...]}`.

### 2.3. Middleware
-   **CORS:** Allow `*` for local development (or specific origins if needed).
-   **Error Handling:** Global exception handler to return JSON errors.

## 3. Implementation Details
-   Use `APIRouter` to organize routes (e.g., `routers/ingest.py`, `routers/chat.py`).
-   Inject dependencies (Storage, VectorStore, Agents) using `Depends`.

## 4. Verification & Definition of Done
-   [ ] Server starts with `uvicorn ai_core.api.main:app`.
-   [ ] Swagger UI is accessible at `http://localhost:8000/docs`.
-   [ ] `/ingest` accepts JSON and saves to DB (verify via SQLite).
-   [ ] `/ask` returns a mock response (until Agent is implemented).
-   [ ] **Manual Test:** Use `curl` or Swagger UI to hit each endpoint.
