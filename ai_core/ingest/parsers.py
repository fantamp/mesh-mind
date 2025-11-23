"""
Модуль парсеров для различных типов документов.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
import email
from email import policy
from email.parser import BytesParser
from pypdf import PdfReader

from ai_core.common.config import settings
from ai_core.common.transcription import TranscriptionService
from ai_core.common.logging import get_logger

logger = get_logger(__name__)


class ParseResult:
    """Результат парсинга документа."""
    def __init__(self, text: str, metadata: Dict[str, Any] = None):
        self.text = text
        self.metadata = metadata or {}


class BaseParser(ABC):
    """Базовый класс для всех парсеров."""
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """
        Парсит файл и возвращает текст с метаданными.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            ParseResult с текстом и метаданными
        """
        pass


class TextParser(BaseParser):
    """Парсер для текстовых файлов (.txt, .md)."""
    
    def parse(self, file_path: Path) -> ParseResult:
        """Читает текстовый файл."""
        logger.info(f"Parsing text file: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        metadata = {
            "source": str(file_path),
            "type": "text",
            "extension": file_path.suffix
        }
        
        return ParseResult(text=text, metadata=metadata)


class PDFParser(BaseParser):
    """Парсер для PDF файлов."""
    
    def parse(self, file_path: Path) -> ParseResult:
        """Извлекает текст из PDF."""
        logger.info(f"Parsing PDF file: {file_path}")
        
        reader = PdfReader(file_path)
        text_parts = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n\n".join(text_parts)
        
        metadata = {
            "source": str(file_path),
            "type": "pdf",
            "pages": len(reader.pages)
        }
        
        return ParseResult(text=full_text, metadata=metadata)


class EmailParser(BaseParser):
    """Парсер для EML файлов."""
    
    def parse(self, file_path: Path) -> ParseResult:
        """
        Парсит EML файл и определяет роль отправителя.
        """
        logger.info(f"Parsing EML file: {file_path}")
        
        with open(file_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        # Извлекаем основные поля
        subject = msg.get("Subject", "")
        from_addr = msg.get("From", "")
        date = msg.get("Date", "")
        
        # Извлекаем тело письма (text/plain предпочтительнее)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
                elif content_type == "text/html" and not body:
                    # Используем HTML только если plain text нет
                    html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    # Упрощенная очистка HTML (для MVP)
                    import re
                    body = re.sub('<[^<]+?>', '', html_body)
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        
        # Определяем роль отправителя
        role = self._detect_role(from_addr)
        
        # Формируем текст
        text = f"Subject: {subject}\n\nFrom: {from_addr}\n\nDate: {date}\n\n{body}"
        
        metadata = {
            "source": str(file_path),
            "type": "email",
            "subject": subject,
            "from": from_addr,
            "date": date,
            "role": role
        }
        
        return ParseResult(text=text, metadata=metadata)
    
    def _detect_role(self, from_addr: str) -> str:
        """
        Определяет роль отправителя на основе домена.
        
        Args:
            from_addr: Email адрес отправителя
            
        Returns:
            "Employee" или "Client"
        """
        # Извлекаем домен из email адреса
        if "@" in from_addr:
            # Обрабатываем формат "Name <email@domain.com>"
            email_part = from_addr.split("<")[-1].split(">")[0].strip()
            domain = email_part.split("@")[-1].lower()
            
            # Проверяем на совпадение с корпоративными доменами
            for company_domain in settings.COMPANY_DOMAINS:
                if domain == company_domain.lower():
                    return "Employee"
        
        return "Client"


class AudioParser(BaseParser):
    """Парсер для аудио файлов."""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
    
    def parse(self, file_path: Path) -> ParseResult:
        """
        Транскрибирует аудио файл в текст.
        """
        logger.info(f"Parsing audio file: {file_path}")
        
        # Делегируем транскрипцию в TranscriptionService
        # Note: transcribe is async, so we need to run it synchronously here
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        text = loop.run_until_complete(self.transcription_service.transcribe(str(file_path)))
        
        metadata = {
            "source": str(file_path),
            "type": "audio",
            "extension": file_path.suffix
        }
        
        return ParseResult(text=text, metadata=metadata)


class DocumentParser:
    """
    Фабрика парсеров - определяет тип файла и выбирает нужный парсер.
    """
    
    # Маппинг расширений на парсеры
    PARSERS = {
        ".txt": TextParser,
        ".md": TextParser,
        ".pdf": PDFParser,
        ".eml": EmailParser,
        ".mp3": AudioParser,
        ".wav": AudioParser,
        ".m4a": AudioParser,
        ".ogg": AudioParser,
    }
    
    @classmethod
    def parse(cls, file_path: Path) -> ParseResult:
        """
        Автоматически определяет тип файла и парсит его.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            ParseResult с текстом и метаданными
            
        Raises:
            ValueError: Если формат файла не поддерживается
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        parser_class = cls.PARSERS.get(extension)
        if not parser_class:
            raise ValueError(f"Unsupported file format: {extension}")
        
        parser = parser_class()
        return parser.parse(file_path)
    
    @classmethod
    def supported_extensions(cls) -> List[str]:
        """Возвращает список поддерживаемых расширений."""
        return list(cls.PARSERS.keys())
