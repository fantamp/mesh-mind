# Specification: Ingestion Service (ai_core/ingest)

## 1. Overview
This module is responsible for parsing various file formats (PDF, MD, TXT, EML) and **Audio files** (via Transcription Service). It prepares them for ingestion into the Vector DB.

## 2. Requirements

### 2.1. File Parsers
-   **Text/Markdown:** Read directly.
-   **PDF:** Use `pypdf` or `pdfminer.six` to extract text.
-   **Email (.eml):** Use Python's built-in `email` library.
    -   Extract `Subject`, `From`, `Date`, and `Body` (text/plain preferred, strip HTML if needed).
    -   **Role Detection:** Check `From` address against `Settings.COMPANY_DOMAINS`. If match, mark as `Employee`, else `Client`.

### 2.2. Chunking
-   **Logic:** Split long texts into chunks for better embedding.
-   **Strategy:** Recursive Character Text Splitter (approx 1000 chars, 200 overlap).
-   **Library:** **Custom simple implementation**. Do NOT use LangChain. A simple function splitting by paragraphs/newlines is sufficient for MVP.

### 2.3. Audio Support
-   **Logic:** If input is an audio file, delegate to `TranscriptionService` to get text, then process as text.

## 3. Implementation Details
-   Create `ai_core/ingest/parsers.py` (Internal module for parsing logic).

## 4. Verification & Definition of Done
-   [ ] PDF parser extracts text from a sample PDF.
-   [ ] EML parser correctly identifies "Client" vs "Employee" based on domain.
-   [ ] Chunker splits a long text into overlapping segments.
-   [ ] CLI script successfully sends data to the running API.
-   [ ] **Manual Test:** Run `python cli/ingest_docs.py --path ./data/sample_docs` and verify they appear in ChromaDB (via Admin UI or script).
