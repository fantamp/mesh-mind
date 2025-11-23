import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot.main import (
    ApiClient,
    start_command,
    summary_command,
    ask_command,
    handle_text_message,
    handle_voice_message,
)

# --- Fixtures ---

@pytest.fixture
def mock_api_client():
    with patch("telegram_bot.main.api_client") as mock:
        mock.ingest_text = AsyncMock()
        mock.ingest_file = AsyncMock()
        mock.summarize = AsyncMock()
        mock.ask = AsyncMock()
        yield mock

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.mention_html.return_value = "Test User"
    update.message = MagicMock(spec=Message)
    update.message.reply_html = AsyncMock()
    update.message.reply_text = AsyncMock()
    update.message.chat = MagicMock(spec=Chat)
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.get_file = AsyncMock()
    return context

# --- ApiClient Tests ---

@pytest.mark.asyncio
async def test_api_client_ingest_text():
    # Mock the client instance inside ApiClient
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Ensure the response is a MagicMock, not AsyncMock, so .json() is synchronous
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response
        
        client = ApiClient("http://test")
        # We need to patch the client instance on the created ApiClient if we mocked the class, 
        # but here we mocked the method on the class, so all instances should use it.
        
        result = await client.ingest_text("hello")
        
        assert result == {"status": "ok"}
        mock_post.assert_called_once()
        # Check arguments. Note: httpx client adds base_url, so the call to post might be relative or absolute depending on implementation.
        # In main.py: url = f"{self.base_url}/ingest", response = await self.client.post(url, ...)
        assert mock_post.call_args[0][0] == "http://test/ingest"
        # Now we use 'data' for multipart/form-data
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
    
    await summary_command(mock_update, mock_context)
    
    mock_api_client.summarize.assert_called_once_with(chat_id=123)
    # Should reply twice: "Generating..." and then the summary
    assert mock_update.message.reply_text.call_count == 2
    assert mock_update.message.reply_text.call_args_list[1][0][0] == "Here is the summary."

@pytest.mark.asyncio
async def test_ask_command_no_args(mock_update, mock_context):
    mock_context.args = []
    await ask_command(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with("Please provide a question: /ask <your question>")

@pytest.mark.asyncio
async def test_ask_command_success(mock_update, mock_context, mock_api_client):
    mock_context.args = ["What", "is", "AI?"]
    mock_api_client.ask.return_value = {"answer": "AI is Artificial Intelligence."}
    mock_update.effective_chat.id = 123
    
    await ask_command(mock_update, mock_context)
    
    mock_api_client.ask.assert_called_once_with("What is AI?", chat_id=123)
    assert mock_update.message.reply_text.call_count == 2
    assert mock_update.message.reply_text.call_args_list[1][0][0] == "AI is Artificial Intelligence."

@pytest.mark.asyncio
async def test_handle_text_message_success(mock_update, mock_context, mock_api_client):
    mock_update.message.text = "Hello world"
    mock_update.effective_user.full_name = "Test User"
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    
    await handle_text_message(mock_update, mock_context)
    
    mock_api_client.ingest_text.assert_called_once_with(
        "Hello world",
        author_name="Test User",
        author_id="123",
        chat_id="456"
    )
    mock_update.message.reply_text.assert_called_once_with("Saved.")

@pytest.mark.asyncio
async def test_handle_voice_message_success(mock_update, mock_context, mock_api_client):
    # Mock voice file
    mock_voice = MagicMock()
    mock_voice.file_id = "voice_123"
    mock_update.message.voice = mock_voice
    mock_update.effective_user.full_name = "Test User"
    
    # Mock get_file
    mock_file = AsyncMock()
    mock_context.bot.get_file.return_value = mock_file
    
    # Mock download_to_drive
    mock_file.download_to_drive.return_value = None
    
    with patch("telegram_bot.main.Path") as mock_path:
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.__truediv__.return_value = mock_path_obj # Mock / operator
        mock_path_obj.exists.return_value = True # For cleanup
        mock_path_obj.__str__.return_value = "/tmp/voice_123.ogg"

        await handle_voice_message(mock_update, mock_context)
        
        mock_context.bot.get_file.assert_called_once_with("voice_123")
        mock_file.download_to_drive.assert_called_once()
        mock_api_client.ingest_file.assert_called_once_with(
            "/tmp/voice_123.ogg",
            author_name="Test User",
            author_id=str(mock_update.effective_user.id),
            chat_id=str(mock_update.effective_chat.id)
        )
        mock_update.message.reply_text.assert_called_once_with("Voice message saved and processing.")
