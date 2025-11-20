# Specification: CLI Tools (cli)

## 1. Overview
A unified command-line interface for managing the Mesh Mind system, primarily used for bulk data ingestion (documents, emails) and system maintenance.

## 2. Requirements

### 2.1. Framework
-   **Library:** `typer` or `argparse`. *Decision: `typer` for better DX and type safety.*
-   **Entry Point:** `cli/main.py`.

### 2.2. Commands

#### `ingest`
-   **Purpose:** Bulk ingest files or emails from a local directory.
-   **Arguments:**
    -   `path`: Path to the directory or file.
    -   `--type`: Optional. Force type (`email`, `doc`). If not provided, infer from extension.
    -   `--recursive`: Boolean (default True).
-   **Logic:**
    1.  Walk the directory.
    2.  For each file, determine type (EML -> email, PDF/MD/TXT -> doc).
    3.  Call the **API** (`POST /ingest`) to process the file.
    4.  Show progress bar (`tqdm`).

### 2.3. Implementation Details
-   The CLI should act as a client to the API for ingestion to ensure consistent logic (parsing, embedding, storage) is applied.

## 3. Verification & Definition of Done
-   [ ] `python cli/main.py --help` shows available commands.
-   [ ] `python cli/main.py ingest ./data/sample_docs` successfully sends files to the API.
-   [ ] Progress bar updates during ingestion.
-   [ ] **Manual Test:** Create a folder with 1 PDF and 1 EML. Run ingest. Verify both appear in the Vector DB (via Admin UI).
