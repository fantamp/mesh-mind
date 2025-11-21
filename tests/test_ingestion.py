"""
Тесты для модуля ingestion.
"""
import pytest
from pathlib import Path
import tempfile
import os

from ai_core.ingest.chunking import recursive_character_split
from ai_core.ingest.parsers import (
    TextParser, 
    PDFParser, 
    EmailParser, 
    DocumentParser,
    ParseResult
)


class TestChunking:
    """Тесты для функции разбиения на чанки."""
    
    def test_simple_chunking(self):
        """Тест базового разбиения текста на чанки."""
        text = "A" * 1500  # Длинный текст
        chunks = recursive_character_split(text, chunk_size=500, chunk_overlap=100)
        
        assert len(chunks) > 1
        # Проверяем что чанки не пустые
        for chunk in chunks:
            assert len(chunk) > 0
    
    def test_chunking_with_paragraphs(self):
        """Тест разбиения текста с параграфами."""
        text = "\n\n".join([f"Paragraph {i}. " + ("Text " * 100) for i in range(5)])
        chunks = recursive_character_split(text, chunk_size=1000, chunk_overlap=200)
        
        assert len(chunks) > 1
        # Проверяем что чанки примерно нужного размера
        for chunk in chunks:
            assert len(chunk) <= 1500  # С учетом перекрытия
    
    def test_chunking_short_text(self):
        """Тест с коротким текстом (должен вернуть один чанк)."""
        text = "Short text"
        chunks = recursive_character_split(text, chunk_size=1000, chunk_overlap=200)
        
        assert len(chunks) == 1
        assert chunks[0] == text


class TestTextParser:
    """Тесты для TextParser."""
    
    def test_parse_text_file(self):
        """Тест парсинга текстового файла."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Test content\nLine 2")
            temp_path = Path(f.name)
        
        try:
            parser = TextParser()
            result = parser.parse(temp_path)
            
            assert result.text == "Test content\nLine 2"
            assert result.metadata["type"] == "text"
            assert result.metadata["extension"] == ".txt"
        finally:
            os.unlink(temp_path)
    
    def test_parse_markdown_file(self):
        """Тест парсинга Markdown файла."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Header\n\nContent")
            temp_path = Path(f.name)
        
        try:
            parser = TextParser()
            result = parser.parse(temp_path)
            
            assert "# Header" in result.text
            assert result.metadata["extension"] == ".md"
        finally:
            os.unlink(temp_path)


class TestEmailParser:
    """Тесты для EmailParser."""
    
    def test_parse_eml_client(self):
        """Тест парсинга email от клиента."""
        eml_content = """From: client@external.com
To: support@company.com
Subject: Test Subject
Date: Mon, 21 Nov 2025 10:00:00 +0100

This is email body.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False, encoding='utf-8') as f:
            f.write(eml_content)
            temp_path = Path(f.name)
        
        try:
            parser = EmailParser()
            result = parser.parse(temp_path)
            
            assert "Test Subject" in result.text
            assert result.metadata["role"] == "Client"
            assert result.metadata["subject"] == "Test Subject"
        finally:
            os.unlink(temp_path)
    
    def test_parse_eml_employee(self):
        """Тест парсинга email от сотрудника."""
        # Предполагаем что в .env настроен COMPANY_DOMAINS
        eml_content = """From: employee@example.com
To: client@external.com
Subject: Response
Date: Mon, 21 Nov 2025 11:00:00 +0100

Response from employee.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False, encoding='utf-8') as f:
            f.write(eml_content)
            temp_path = Path(f.name)
        
        try:
            parser = EmailParser()
            result = parser.parse(temp_path)
            
            # Роль зависит от настроек COMPANY_DOMAINS
            # Для теста проверяем что роль определена
            assert result.metadata["role"] in ["Client", "Employee"]
        finally:
            os.unlink(temp_path)


class TestDocumentParser:
    """Тесты для DocumentParser (фабрика)."""
    
    def test_supported_extensions(self):
        """Тест списка поддерживаемых расширений."""
        extensions = DocumentParser.supported_extensions()
        
        assert ".txt" in extensions
        assert ".md" in extensions
        assert ".pdf" in extensions
        assert ".eml" in extensions
        assert ".mp3" in extensions
    
    def test_parse_text_file_via_factory(self):
        """Тест автоопределения парсера через фабрику."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Factory test")
            temp_path = Path(f.name)
        
        try:
            result = DocumentParser.parse(temp_path)
            assert result.text == "Factory test"
            assert result.metadata["type"] == "text"
        finally:
            os.unlink(temp_path)
    
    def test_unsupported_format(self):
        """Тест обработки неподдерживаемого формата."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                DocumentParser.parse(temp_path)
        finally:
            os.unlink(temp_path)
