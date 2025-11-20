# Specification: Data Storage Layer (ai_core/storage)

## 1. Overview
This module manages persistent storage for the application, specifically the SQLite database for structured data and the File System for unstructured media/documents.

## 2. Requirements

### 2.1. SQLite Database (`db.py`)
-   **Library:** `sqlmodel` (Async).
-   **Rationale:** Simplifies code by combining Pydantic models and SQLAlchemy schemas. No need for separate Alembic migrations for this MVP (use `SQLModel.metadata.create_all`).
-   **Schema:**
    -   **Table `messages`**:
        -   `id` (PK, String/UUID)
        -   `source` (String, index)
        -   `chat_id` (String, index)
        -   `author_name` (String)
        -   `content` (Text)
        -   `created_at` (DateTime, index)
        -   `media_path` (String, nullable)
        -   `media_type` (String, nullable)
    -   **Table `chat_state`**:
        -   `chat_id` (PK, String)
        -   `last_summary_message_id` (String, nullable) - ID of the last message included in a summary.
        -   `updated_at` (DateTime)

    -   **Table `documents`** (Metadata for files):
        -   `id` (PK, String/UUID)
        -   `filename` (String)
        -   `file_path` (String)
        -   `upload_date` (DateTime)
        - `GEMINI_MODEL_SMART`: Default `gemini-2.5-pro` (User requirement).
        -   `COMPANY_DOMAINS`: List of domains to identify employees (e.g., `["mycompany.com"]`).*
-   **Functionality:**
    -   `init_db()`: Create tables if not exist.
    -   `save_message(msg: Message)`: Async insert.
    -   `get_messages(limit, offset, filter)`: Async select.
    -   `get_chat_state(chat_id)`: Get last summary point.
    -   `update_chat_state(chat_id, last_msg_id)`: Update summary point.
    -   `save_document_metadata(doc: Document)`: Async insert.

### 2.2. File System Storage (`fs.py`)
-   **Functionality:**
    -   Manage directory structure:
        -   `data/media/voice/{YYYY}/{MM}/{DD}/`
        -   `data/docs/`
    -   `save_file(file_content: bytes, filename: str, type: str) -> str`: Saves file and returns absolute path.
    -   Ensure unique filenames (append UUID or timestamp).

## 3. Implementation Details
-   Use `ai_core/common/config.py` to get paths.
-   Ensure `data/` directory is created on startup if missing.

## 4. Verification & Definition of Done
-   [ ] Database file `mesh_mind.db` is created in the configured path.
-   [ ] Tables `messages` and `documents` exist with correct columns.
-   [ ] Can insert a message and retrieve it via Python script.
-   [ ] Can save a dummy file and verify it exists on disk in the correct YYYY/MM/DD folder.
-   [ ] **Manual Test:** Run `tests/manual/test_storage.py` which performs an insert/select cycle and a file save operation.
