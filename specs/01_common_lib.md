# Specification: Common Library (ai_core/common)

## 1. Overview
This module provides shared utilities, configuration management, logging, and data models used across the entire `ai_core` service and potentially CLI tools. It ensures consistency and reduces code duplication.

## 2. Requirements

### 2.1. Configuration Management (`config.py`)
-   **Library:** Use `pydantic-settings` for robust environment variable parsing.
-   **Functionality:**
    -   Load settings from `.env` file.
    -   Define a `Settings` class with typed fields.
    -   **Required Fields:**
        -   `ENV`: (dev, prod)
        -   `LOG_LEVEL`: (DEBUG, INFO, WARNING, ERROR)
        -   `DB_PATH`: Path to SQLite database (default: `data/db/mesh_mind.db`)
        -   `CHROMA_PATH`: Path to Vector DB (default: `data/vector_store`)
        -   `MEDIA_PATH`: Path to media storage (default: `data/media`)
        -   `GOOGLE_API_KEY`: For Gemini.
        -   `GEMINI_MODEL_FAST`: Default `gemini-2.5-flash` (User requirement).
        - `GEMINI_MODEL_SMART`: Default `gemini-2.5-pro` (User requirement).
        -   `COMPANY_DOMAINS`: List of domains to identify employees (e.g., `["mycompany.com"]`).
-   **Validation:** Fail fast if critical keys (like `GOOGLE_API_KEY`) are missing.

### 2.2. Logging (`logging.py`)
-   **Library:** Standard `logging` or `loguru` (preferred for simplicity and color output).
-   **Functionality:**
    -   Provide a `setup_logging()` function.
    -   Console output with appropriate formatting.
    -   File output (optional, rotating file handler in `logs/`).
    -   Support JSON formatting for production (optional but good practice).

### 2.3. Data Models (`models.py`)
-   **Library:** `sqlmodel` (combines Pydantic and SQLAlchemy).
-   **Core Entities:**
    -   Define models as `SQLModel` classes (table=True for DB, table=False for Pydantic-only schemas).
    -   `Message`: Represents a chat message.
        -   `id`: str (UUID or Telegram ID)
        -   `source`: str (e.g., "telegram", "email")
        -   `author_id`: str
        -   `author_name`: str
        -   `content`: str
        -   `timestamp`: datetime
        -   `media_path`: Optional[str]
        -   `media_type`: Optional[str] (voice, document - NO images)
    -   `Document`: Represents an ingested document.
        -   `id`: str
        -   `filename`: str
        -   `content`: str
        -   `metadata`: dict (tags, author, date)

## 3. Implementation Details
-   Create `ai_core/common/` directory.
-   Implement `__init__.py` to expose key components.
-   Ensure zero circular dependencies.

## 4. Verification & Definition of Done
-   [ ] `Settings` class loads correctly from a sample `.env` file.
-   [ ] Missing `GOOGLE_API_KEY` raises a validation error.
-   [ ] Logging works: `logger.info("test")` prints formatted output to console.
-   [ ] Pydantic models validate correct data and reject invalid data.
-   [ ] **Manual Test:** Create a script `tests/manual/test_common.py` that initializes settings and logs a message. Run it successfully.
