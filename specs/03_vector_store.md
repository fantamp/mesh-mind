# Specification: Vector Store (ai_core/rag)

## 1. Overview
This module handles the semantic search capability (RAG). It manages the ChromaDB instance, embedding generation, and document retrieval.

## 2. Requirements

### 2.1. Vector Database (`vector_db.py`)
-   **Library:** `chromadb`.
-   **Configuration:**
    -   Persistent Client.
    -   Path from `Settings.CHROMA_PATH`.
-   **Collections:**
    -   `knowledge_base`: For documents and long-term info.
    -   `chat_history`: For chat messages (optional, if we want semantic search over chat). *Decision: Put everything in one collection with metadata `type` ("doc" or "chat") for simplicity, or two separate ones. Let's use one collection `mesh_mind_v1` with metadata filtering.*

### 2.2. Embeddings
-   **Provider:** Google Gemini Embeddings (`models/text-embedding-004` or similar).
-   **Implementation:**
    -   Use `google-generativeai` library or `langchain-google-genai` if using LangChain. *Decision: Use `google-generativeai` directly to minimize dependencies unless LangChain is strictly needed for other agents.*
    -   Create a wrapper `EmbeddingService` that takes text and returns vector.

### 2.3. Functionality
-   `add_texts(texts: List[str], metadata: List[dict])`: Generate embeddings and add to DB.
-   `search(query: str, n_results: int = 5, filters: dict = None)`: Generate query embedding and search.
    -   Support filtering by `type` (e.g., only search documents, or only chat).
    -   Support filtering by `tags` (for documents).

## 3. Implementation Details
-   Handle rate limits for Embedding API (simple retry logic).
-   Ensure metadata includes `source`, `date`, `author`, `tags`.

## 4. Verification & Definition of Done
-   [ ] ChromaDB is initialized in `data/vector_store`.
-   [ ] Can add a text "Hello world" and search for "Greeting".
-   [ ] Search returns relevant results with correct metadata.
-   [ ] Metadata filtering works (e.g., search only `type="doc"`).
-   [ ] **Manual Test:** Run `tests/manual/test_vector.py` which ingests 3 sample texts and queries them, printing results.
