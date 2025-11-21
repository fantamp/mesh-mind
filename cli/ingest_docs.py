#!/usr/bin/env python3
"""
CLI скрипт для загрузки документов в Vector Store.

Usage:
    python cli/ingest_docs.py --path ./data/sample_docs
"""
import argparse
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_core.ingest.parsers import DocumentParser
from ai_core.ingest.chunking import recursive_character_split
from ai_core.rag.vector_db import VectorDB
from ai_core.common.logging import get_logger

logger = get_logger(__name__)


def ingest_document(file_path: Path, vector_db: VectorDB):
    """
    Обрабатывает один документ: парсит, разбивает на чанки, загружает в Vector Store.
    
    Args:
        file_path: Путь к файлу
        vector_db: Экземпляр VectorDB
    """
    try:
        # Парсим документ
        logger.info(f"Processing file: {file_path}")
        result = DocumentParser.parse(file_path)
        
        # Разбиваем на чанки
        chunks = recursive_character_split(result.text)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Подготавливаем метаданные для каждого чанка
        metadatas = []
        for i in range(len(chunks)):
            chunk_metadata = result.metadata.copy()
            chunk_metadata["chunk_index"] = i
            metadatas.append(chunk_metadata)
        
        # Добавляем в Vector Store
        vector_db.add_texts(chunks, metadatas)
        logger.info(f"Successfully ingested: {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to ingest {file_path}: {e}")


def ingest_directory(directory: Path, vector_db: VectorDB):
    """
    Рекурсивно обрабатывает все поддерживаемые файлы в директории.
    
    Args:
        directory: Путь к директории
        vector_db: Экземпляр VectorDB
    """
    supported_exts = DocumentParser.supported_extensions()
    
    # Собираем все файлы с поддерживаемыми расширениями
    files = []
    for ext in supported_exts:
        files.extend(directory.rglob(f"*{ext}"))
    
    logger.info(f"Found {len(files)} files to process")
    
    for file_path in files:
        ingest_document(file_path, vector_db)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into Vector Store"
    )
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to file or directory to ingest"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="default",
        help="Collection name in Vector Store (default: 'default')"
    )
    
    args = parser.parse_args()
    path = Path(args.path)
    
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        sys.exit(1)
    
    # Инициализируем VectorDB
    logger.info(f"Initializing VectorDB")
    vector_db = VectorDB()
    
    # Обрабатываем файл или директорию
    if path.is_file():
        ingest_document(path, vector_db)
    elif path.is_dir():
        ingest_directory(path, vector_db)
    else:
        logger.error(f"Invalid path: {path}")
        sys.exit(1)
    
    logger.info("Ingestion complete!")


if __name__ == "__main__":
    main()
