"""
CLI-инструмент для bulk-импорта данных в Mesh Mind.

Использование:
    python cli/main.py ingest ./data/sample_docs
    python cli/main.py ingest ./data/sample.pdf --type doc
    python cli/main.py ingest ./emails --recursive
"""
import json
from pathlib import Path
from typing import Optional, List

import typer
import httpx
from tqdm import tqdm
from loguru import logger

app = typer.Typer(help="Mesh Mind CLI Tools")

# Поддерживаемые расширения файлов (соответствуют DocumentParser)
SUPPORTED_EXTENSIONS = {
    # Документы
    ".txt": "doc",
    ".md": "doc",
    ".pdf": "doc",
    # Email
    ".eml": "email",
    # Аудио
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".ogg": "audio",
}


def collect_files(path: Path, recursive: bool = True) -> List[Path]:
    """
    Собирает все файлы из указанного пути.
    
    Args:
        path: Путь к файлу или директории
        recursive: Рекурсивный обход директорий
    
    Returns:
        Список путей к файлам
    """
    files = []
    
    if path.is_file():
        files.append(path)
    elif path.is_dir():
        if recursive:
            # Рекурсивный обход всех поддерживаемых файлов
            for ext in SUPPORTED_EXTENSIONS.keys():
                files.extend(path.rglob(f"*{ext}"))
        else:
            # Только файлы в текущей директории
            for ext in SUPPORTED_EXTENSIONS.keys():
                files.extend(path.glob(f"*{ext}"))
    
    return sorted(set(files))  # Удаляем дубликаты и сортируем


def determine_file_type(file_path: Path, force_type: Optional[str] = None) -> str:
    """
    Определяет тип файла на основе расширения или принудительного типа.
    
    Args:
        file_path: Путь к файлу
        force_type: Принудительный тип (email, doc, audio)
    
    Returns:
        Тип файла: "email", "doc", "audio"
    """
    if force_type:
        return force_type
    
    extension = file_path.suffix.lower()
    return SUPPORTED_EXTENSIONS.get(extension, "doc")


def send_file_to_api(
    file_path: Path, 
    api_url: str, 
    file_type: str
) -> dict:
    """
    Отправляет файл на API для обработки.
    
    Args:
        file_path: Путь к файлу
        api_url: Base URL API
        file_type: Тип файла (email, doc, audio)
    
    Returns:
        Ответ от API
    
    Raises:
        httpx.HTTPError: При ошибке HTTP-запроса
    """
    # Формируем metadata для API
    metadata = {
        "source": "cli",
        "author_id": "cli_user",
        "author_name": "CLI Import",
        "chat_id": "cli_imports",
    }
    
    # Открываем файл и отправляем
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, get_mime_type(file_path))}
        data = {"metadata": json.dumps(metadata)}
        
        response = httpx.post(
            f"{api_url}/ingest",
            files=files,
            data=data,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


def get_mime_type(file_path: Path) -> str:
    """
    Определяет MIME-тип файла на основе расширения.
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        MIME-тип
    """
    extension = file_path.suffix.lower()
    
    mime_types = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".eml": "message/rfc822",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }
    
    return mime_types.get(extension, "application/octet-stream")


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to file or directory to ingest"),
    type: Optional[str] = typer.Option(
        None, 
        help="Force file type: 'email', 'doc', or 'audio'. Auto-detected if not specified."
    ),
    recursive: bool = typer.Option(
        True, 
        help="Recursively process directories"
    ),
    api_url: str = typer.Option(
        "http://localhost:8000/api",
        help="Base URL of the Mesh Mind API"
    ),
):
    """
    Bulk ingest files (documents, emails, audio) into Mesh Mind.
    
    Examples:
        python cli/main.py ingest ./data/sample_docs
        python cli/main.py ingest ./data/sample.pdf --type doc
        python cli/main.py ingest ./emails --no-recursive
    """
    # Проверяем существование пути
    if not path.exists():
        typer.echo(f"❌ Error: Path does not exist: {path}", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"📂 Collecting files from: {path}")
    typer.echo(f"🔄 Recursive: {recursive}")
    
    # Собираем файлы
    files = collect_files(path, recursive=recursive)
    
    if not files:
        typer.echo("⚠️  No supported files found.")
        typer.echo(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        raise typer.Exit(code=0)
    
    typer.echo(f"✅ Found {len(files)} file(s) to process\n")
    
    # Обрабатываем файлы с progress bar
    success_count = 0
    error_count = 0
    
    with tqdm(files, desc="Processing files", unit="file") as pbar:
        for file_path in pbar:
            try:
                # Определяем тип файла
                file_type = determine_file_type(file_path, type)
                
                # Обновляем описание прогресс-бара
                pbar.set_postfix_str(f"{file_path.name}")
                
                # Отправляем на API
                result = send_file_to_api(file_path, api_url, file_type)
                
                logger.info(f"✓ Ingested: {file_path.name} (id: {result.get('id')})")
                success_count += 1
                
            except httpx.HTTPError as e:
                logger.error(f"✗ Failed to ingest {file_path.name}: {e}")
                error_count += 1
            except Exception as e:
                logger.error(f"✗ Unexpected error for {file_path.name}: {e}")
                error_count += 1
    
    # Итоговая статистика
    typer.echo(f"\n{'='*50}")
    typer.echo(f"📊 Summary:")
    typer.echo(f"   ✅ Success: {success_count}")
    typer.echo(f"   ❌ Errors:  {error_count}")
    typer.echo(f"   📁 Total:   {len(files)}")
    typer.echo(f"{'='*50}")
    
    if error_count > 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
