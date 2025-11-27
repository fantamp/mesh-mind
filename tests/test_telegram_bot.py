import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot.api_client import ApiClient
from telegram_bot.utils import parse_summary_params
from telegram_bot.handlers import (
    start_command,
    summary_command,
    ask_command,
    handle_text_message,
    handle_voice_message,
    help_command,
)

# --- Fixtures ---

@pytest.fixture
def mock_api_client():
    # We mock the class so we can inspect calls
    mock = MagicMock(spec=ApiClient)
    mock.ingest_text = AsyncMock()
    mock.ingest_file = AsyncMock()
    mock.summarize = AsyncMock()
    mock.ask = AsyncMock()
    mock.chat_message = AsyncMock()
    return mock

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.mention_html.return_value = "Test User"
    update.message = MagicMock(spec=Message)
    update.message.reply_html = AsyncMock()
    update.message.reply_text = AsyncMock()
    update.message.chat = MagicMock(spec=Chat)
    # Ensure message is not treated as forwarded in tests unless explicitly set
    update.message.forward_origin = None
    update.message.forward_from = None
    update.message.forward_sender_name = None
    update.message.forward_from_chat = None
    return update

@pytest.fixture
def mock_context(mock_api_client):
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.get_file = AsyncMock()
    # job_queue mock for forward debounce
    mock_job = MagicMock()
    mock_job.schedule_removal = MagicMock()
    job_queue = MagicMock()
    job_queue.run_once.return_value = mock_job
    context.job_queue = job_queue
    
    # Mock bot_data and chat_data
    context.bot_data = {"api_client": mock_api_client}
    context.chat_data = {}
    
    return context

# --- ApiClient Tests ---

@pytest.mark.asyncio
async def test_api_client_ingest_text():
    # Mock httpx.AsyncClient inside ApiClient
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response
        
        client = ApiClient("http://test")
        
        result = await client.ingest_text("hello")
        
        assert result == {"status": "ok"}
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "http://test/ingest"
        assert "text" in mock_post.call_args[1]["data"]
        assert mock_post.call_args[1]["data"]["text"] == "hello"

@pytest.mark.asyncio
async def test_api_client_summarize():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"summary": "test summary"}
        mock_post.return_value = mock_response
        
        client = ApiClient("http://test")
        result = await client.summarize(chat_id=123)
        
        assert result == {"summary": "test summary"}
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "http://test/summarize"
        assert mock_post.call_args[1]["json"] == {"chat_id": 123}

# --- Handler Tests ---

@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    await start_command(mock_update, mock_context)
    mock_update.message.reply_html.assert_called_once()
    assert "Test User" in mock_update.message.reply_html.call_args[0][0]

@pytest.mark.asyncio
async def test_summary_command_success(mock_update, mock_context, mock_api_client):
    mock_api_client.summarize.return_value = {"summary": "Here is the summary."}
    mock_update.effective_chat.id = 123
    mock_context.args = []  # Дефолтные аргументы (auto режим)
    
    # Need to allow non-whitelisted chats for testing
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True):
        await summary_command(mock_update, mock_context)
    
    # Проверяем что summarize был вызван
    mock_api_client.summarize.assert_called_once()
    # Should reply twice: "Generating..." and then the summary
    assert mock_update.message.reply_text.call_count == 2
    assert mock_update.message.reply_text.call_args_list[1][0][0] == "Here is the summary."


@pytest.mark.asyncio
async def test_ask_command_no_args(mock_update, mock_context):
    mock_context.args = []
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True):
        await ask_command(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with("Please provide a question: /ask <your question>")

@pytest.mark.asyncio
async def test_ask_command_success(mock_update, mock_context, mock_api_client):
    mock_context.args = ["What", "is", "AI?"]
    mock_api_client.ask.return_value = {"answer": "AI is Artificial Intelligence."}
    mock_update.effective_chat.id = 123
    
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True):
        await ask_command(mock_update, mock_context)
    
    mock_api_client.ask.assert_called_once_with("What is AI?", chat_id=123)
    assert mock_update.message.reply_text.call_count == 2
    assert mock_update.message.reply_text.call_args_list[1][0][0] == "AI is Artificial Intelligence."

@pytest.mark.asyncio
async def test_handle_text_message_success(mock_update, mock_context, mock_api_client):
    mock_update.message.text = "Hello world"
    mock_update.effective_user.full_name = "Test User"
    mock_update.effective_user.id = 123
    mock_update.effective_user.username = "nick"
    mock_update.effective_chat.id = 456
    
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True):
        await handle_text_message(mock_update, mock_context)
    
    mock_api_client.ingest_text.assert_not_called()
    mock_api_client.chat_message.assert_called_once()
    # reply_text called either with reply or Saved.; at least once
    assert mock_update.message.reply_text.call_count >= 1

@pytest.mark.asyncio
async def test_handle_voice_message_success(mock_update, mock_context, mock_api_client):
    # Mock voice file
    mock_voice = MagicMock()
    mock_voice.file_id = "voice_123"
    mock_update.message.voice = mock_voice
    mock_update.effective_user.full_name = "Test User"
    mock_update.effective_user.username = "nick"
    mock_api_client.ingest_file.return_value = {"status": "ok", "text": "transcribed text"}
    
    # Mock get_file
    mock_file = AsyncMock()
    mock_context.bot.get_file.return_value = mock_file
    
    # Mock download_to_drive
    mock_file.download_to_drive.return_value = None
    
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True), \
         patch("telegram_bot.handlers.Path") as mock_path:
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.__truediv__.return_value = mock_path_obj # Mock / operator
        mock_path_obj.exists.return_value = True # For cleanup
        mock_path_obj.__str__.return_value = "/tmp/voice_123.ogg"

        await handle_voice_message(mock_update, mock_context)
        
        mock_context.bot.get_file.assert_called_once_with("voice_123")
        mock_file.download_to_drive.assert_called_once()
        mock_api_client.ingest_file.assert_called_once()
        mock_api_client.chat_message.assert_called_once()
        assert mock_update.message.reply_text.call_count >= 1

# --- parse_summary_params Tests ---

def test_parse_summary_params_empty():
    """Тест автоопределения разговора при пустых аргументах"""
    result = parse_summary_params([])
    assert result["mode"] == "auto"

def test_parse_summary_params_count():
    """Тест парсинга количества сообщений"""
    result = parse_summary_params(["20"])
    assert result["mode"] == "count"
    assert result["value"] == 20

def test_parse_summary_params_hours():
    """Тест парсинга временного интервала в часах"""
    result = parse_summary_params(["2h"])
    assert result["mode"] == "time"
    assert result["hours"] == 2

def test_parse_summary_params_minutes():
    """Тест парсинга временного интервала в минутах"""
    result = parse_summary_params(["30m"])
    assert result["mode"] == "time"
    assert result["minutes"] == 30

def test_parse_summary_params_invalid():
    """Тест некорректного формата - должен вернуть auto режим"""
    result = parse_summary_params(["invalid_format"])
    assert result["mode"] == "auto"

# --- Reply-based summary Tests ---

@pytest.mark.asyncio
async def test_summary_command_with_reply(mock_update, mock_context, mock_api_client):
    """Тест команды /summary с reply на сообщение"""
    from datetime import datetime, timezone
    
    mock_api_client.summarize.return_value = {"summary": "Summary from replied message."}
    mock_update.effective_chat.id = 123
    mock_context.args = []
    
    # Мокаем reply_to_message
    mock_reply_message = MagicMock()
    mock_reply_message.date = datetime(2025, 11, 24, 8, 0, 0, tzinfo=timezone.utc)
    mock_update.message.reply_to_message = mock_reply_message
    
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True):
        await summary_command(mock_update, mock_context)
    
    # Проверяем что summarize был вызван с since_datetime из reply
    mock_api_client.summarize.assert_called_once()
    call_kwargs = mock_api_client.summarize.call_args.kwargs
    assert "since_datetime" in call_kwargs
    assert call_kwargs["chat_id"] == 123
    
    # Проверяем что был ответ пользователю
    assert mock_update.message.reply_text.call_count == 2
    assert mock_update.message.reply_text.call_args_list[1][0][0] == "Summary from replied message."


# --- help_command Tests ---

@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    """Тест команды /help"""
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True):
        await help_command(mock_update, mock_context)
    
    # Проверяем что был вызван reply_text с текстом справки
    mock_update.message.reply_text.assert_called_once()
    help_text = mock_update.message.reply_text.call_args[0][0]
    
    # Проверяем что в справке есть все основные команды
    assert "/start" in help_text
    assert "/help" in help_text
    assert "/summary" in help_text
    assert "/ask" in help_text
