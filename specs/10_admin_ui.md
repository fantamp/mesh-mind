# Specification: Admin UI (ai_core/ui)

## 1. Overview
This is a Streamlit application that allows administrators to manage the Knowledge Base, view logs/stats, and manually test the agents.

## 2. Requirements

### 2.1. Framework
-   **Library:** `streamlit`.
-   **Run:** `streamlit run ai_core/ui/main.py`.

### 2.2. Pages

#### **Home / Dashboard**
-   Show stats: Total messages, Total documents, Last ingestion time.

#### **Knowledge Base (RAG)**
-   **View:** Table of documents in ChromaDB (id, filename, tags, type).
-   **Search:** Input field to semantic search chunks.
-   **Upload:** Drag & Drop file uploader.
    -   Action: Call `POST /ingest` (or internal service) to parse and save.
    -   **Tagging:** Input field to add tags (e.g., "Law", "Manual") before uploading.

#### **Chat / Playground**
-   **Interface:** Chat-like UI.
-   **Mode Selector:** "QA Agent" vs "Summarizer".
-   **Action:** Send query to API and show response.
-   **Debug:** Show "Sources" used for the answer.

### 2.3. Authentication
-   **None** for this PoC phase (as per user request).

## 3. Implementation Details
-   Use `requests` to call the local API (`http://localhost:8000`) to keep UI decoupled from Core logic (optional, but cleaner). Or import `ai_core` modules directly if running in same process. *Decision: Import modules directly for simplicity in PoC, or use API if running separately. Let's use API calls to verify the API is working.*

## 4. Verification & Definition of Done
-   [ ] Streamlit app starts without errors.
-   [ ] Can upload a file with a tag "Test" and see it in the list.
-   [ ] Can search for a phrase and see relevant chunks.
-   [ ] Can ask a question in the Playground and get an answer.
-   [ ] **Manual Test:** Open `http://localhost:8501`, upload a PDF, ask a question about it.
