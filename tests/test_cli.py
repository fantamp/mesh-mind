"""
Unit-тесты для CLI-инструмента.
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import httpx

from cli.main import (
    collect_files,
    determine_file_type,
    send_file_to_api,
    get_mime_type,
    SUPPORTED_EXTENSIONS,
)


class TestCollectFiles:
    """Тесты для collect_files()"""
    
    def test_collect_single_file(self, tmp_path):
        """Проверка сбора одного файла"""
        # Создаем тестовый файл
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Собираем файлы
        files = collect_files(test_file, recursive=True)
        
        assert len(files) == 1
        assert files[0] == test_file
    
    def test_collect_directory_non_recursive(self, tmp_path):
        """Проверка сбора файлов без рекурсии"""
        # Создаем структуру:
        # tmp_path/
        #   file1.txt
        #   file2.pdf
        #   subdir/
        #     file3.txt
        
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.pdf").write_text("content2")
        
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        # Собираем без рекурсии
        files = collect_files(tmp_path, recursive=False)
        
        assert len(files) == 2
        assert all(f.parent == tmp_path for f in files)
    
    def test_collect_directory_recursive(self, tmp_path):
        """Проверка рекурсивного сбора файлов"""
        # Создаем вложенную структуру
        (tmp_path / "file1.txt").write_text("content1")
        
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.md").write_text("content2")
        
        nested = subdir / "nested"
        nested.mkdir()
        (nested / "file3.eml").write_text("content3")
        
        # Собираем рекурсивно
        files = collect_files(tmp_path, recursive=True)
        
        assert len(files) == 3
        assert any(f.name == "file3.eml" for f in files)
    
    def test_collect_filters_unsupported_extensions(self, tmp_path):
        """Проверка фильтрации неподдерживаемых расширений"""
        (tmp_path / "supported.txt").write_text("ok")
        (tmp_path / "unsupported.xyz").write_text("skip")
        (tmp_path / "image.jpg").write_text("skip")
        
        files = collect_files(tmp_path, recursive=False)
        
        assert len(files) == 1
        assert files[0].name == "supported.txt"


class TestDetermineFileType:
    """Тесты для determine_file_type()"""
    
    def test_force_type(self):
        """Проверка принудительного типа"""
        file_path = Path("test.txt")
        result = determine_file_type(file_path, force_type="email")
        assert result == "email"
    
    def test_auto_detect_doc(self):
        """Проверка автоопределения типа doc"""
        assert determine_file_type(Path("test.txt")) == "doc"
        assert determine_file_type(Path("test.md")) == "doc"
        assert determine_file_type(Path("test.pdf")) == "doc"
    
    def test_auto_detect_email(self):
        """Проверка автоопределения типа email"""
        assert determine_file_type(Path("test.eml")) == "email"
    
    def test_auto_detect_audio(self):
        """Проверка автоопределения типа audio"""
        assert determine_file_type(Path("test.mp3")) == "audio"
        assert determine_file_type(Path("test.wav")) == "audio"
        assert determine_file_type(Path("test.ogg")) == "audio"
        assert determine_file_type(Path("test.m4a")) == "audio"


class TestGetMimeType:
    """Тесты для get_mime_type()"""
    
    def test_text_files(self):
        """Проверка MIME-типов для текстовых файлов"""
        assert get_mime_type(Path("test.txt")) == "text/plain"
        assert get_mime_type(Path("test.md")) == "text/markdown"
    
    def test_pdf(self):
        """Проверка MIME-типа для PDF"""
        assert get_mime_type(Path("test.pdf")) == "application/pdf"
    
    def test_email(self):
        """Проверка MIME-типа для email"""
        assert get_mime_type(Path("test.eml")) == "message/rfc822"
    
    def test_audio_files(self):
        """Проверка MIME-типов для аудио"""
        assert get_mime_type(Path("test.mp3")) == "audio/mpeg"
        assert get_mime_type(Path("test.wav")) == "audio/wav"
        assert get_mime_type(Path("test.m4a")) == "audio/mp4"
        assert get_mime_type(Path("test.ogg")) == "audio/ogg"
    
    def test_unknown_extension(self):
        """Проверка неизвестного расширения"""
        assert get_mime_type(Path("test.xyz")) == "application/octet-stream"


class TestSendFileToAPI:
    """Тесты для send_file_to_api()"""
    
    def test_send_file_success(self, tmp_path):
        """Проверка успешной отправки файла"""
        # Создаем тестовый файл
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Mock HTTP-ответ
        with patch("cli.main.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "ok", "id": "test-id-123"}
            mock_post.return_value = mock_response
            
            # Отправляем файл
            result = send_file_to_api(
                test_file,
                "http://localhost:8000/api",
                "doc"
            )
            
            # Проверки
            assert result["status"] == "ok"
            assert result["id"] == "test-id-123"
            
            # Проверяем что был вызван POST
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Проверяем URL
            assert call_args[0][0] == "http://localhost:8000/api/ingest"
            
            # Проверяем metadata
            metadata_str = call_args[1]["data"]["metadata"]
            metadata = json.loads(metadata_str)
            assert metadata["source"] == "cli"
            assert metadata["chat_id"] == "cli_imports"
    
    def test_send_file_http_error(self, tmp_path):
        """Проверка обработки HTTP-ошибки"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        with patch("cli.main.httpx.post") as mock_post:
            # Симулируем HTTP-ошибку
            mock_post.side_effect = httpx.HTTPError("API Error")
            
            # Проверяем что исключение пробрасывается
            with pytest.raises(httpx.HTTPError):
                send_file_to_api(
                    test_file,
                    "http://localhost:8000/api",
                    "doc"
                )


class TestSupportedExtensions:
    """Тесты для константы SUPPORTED_EXTENSIONS"""
    
    def test_has_required_extensions(self):
        """Проверка наличия всех требуемых расширений"""
        required = [".txt", ".md", ".pdf", ".eml", ".mp3", ".wav", ".m4a", ".ogg"]
        
        for ext in required:
            assert ext in SUPPORTED_EXTENSIONS, f"Missing extension: {ext}"
    
    def test_extension_mapping(self):
        """Проверка правильности маппинга расширений"""
        assert SUPPORTED_EXTENSIONS[".txt"] == "doc"
        assert SUPPORTED_EXTENSIONS[".eml"] == "email"
        assert SUPPORTED_EXTENSIONS[".mp3"] == "audio"
        assert SUPPORTED_EXTENSIONS[".ogg"] == "audio"
