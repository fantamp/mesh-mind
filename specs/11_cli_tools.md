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

## 4. Дополнительные ресурсы

### Typer
-   [Официальная документация](https://typer.tiangolo.com/) — основной ресурс по Typer
-   [First Steps Tutorial](https://typer.tiangolo.com/tutorial/first-steps/) — быстрый старт
-   [Arguments & Options](https://typer.tiangolo.com/tutorial/arguments/) — работа с аргументами командной строки
-   [Commands & Groups](https://typer.tiangolo.com/tutorial/commands/) — создание подкоманд
-   [Progress Bar](https://typer.tiangolo.com/tutorial/progressbar/) — интеграция с прогресс-барами
-   Текущая версия: **0.20.0** (выпущена в октябре 2025)

**Ключевые особенности:**
-   Построен на основе type hints (Python 3.6+)
-   Автоматическая генерация `--help`
-   CLI-версия FastAPI (тот же автор)
-   Отличная интеграция с `rich` для красивого вывода

### tqdm (для progress bar)
-   [Официальная документация](https://tqdm.github.io/) — подробная документация
-   [GitHub Repository](https://github.com/tqdm/tqdm) — репозиторий с примерами
-   [PyPI](https://pypi.org/project/tqdm/) — установка и основная информация

**Основные возможности:**
-   Обертка для итераторов: `for item in tqdm(items):`
-   Очень низкий overhead (~60ns на итерацию)
-   Работает в консоли, Jupyter, GUI
-   Не требует зависимостей

**Пример использования:**
```python
from tqdm import tqdm
import time

for i in tqdm(range(100), desc="Processing files"):
    time.sleep(0.1)
```

### requests (для HTTP-запросов к API)
-   [Официальная документация](https://requests.readthedocs.io/) — библиотека для HTTP-запросов
-   Текущая версия: **2.32.5**

**Альтернатива:** `httpx` — если нужна асинхронность или HTTP/2 поддержка.
