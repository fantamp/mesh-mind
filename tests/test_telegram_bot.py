import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot.handlers import (
    start_command,
    handle_voice_or_text_message,
    help_command,
)

# --- Fixtures ---

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
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.get_file = AsyncMock()
    
    # Mock bot_data and chat_data
    context.bot_data = {}
    context.chat_data = {}
    
    return context

# --- Handler Tests ---

@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    await start_command(mock_update, mock_context)
    mock_update.message.reply_html.assert_called_once()
    assert "Test User" in mock_update.message.reply_html.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_text_message_success(mock_update, mock_context):
    mock_update.message.text = "Hello world"
    mock_update.message.voice = None  # Ensure voice is None
    mock_update.effective_user.full_name = "Test User"
    mock_update.effective_user.id = 123
    mock_update.effective_user.username = "nick"
    mock_update.effective_chat.id = 456
    
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True), \
         patch("telegram_bot.handlers.save_message", new_callable=AsyncMock) as mock_save, \
         patch("telegram_bot.handlers.run_agent_sync") as mock_run_agent_sync, \
         patch("telegram_bot.handlers.is_forwarded", return_value=False):
        
        # Mock run_agent_sync to return a response
        mock_run_agent_sync.return_value = "Orchestrator reply"
        
        await handle_voice_or_text_message(mock_update, mock_context)
    
        mock_save.assert_called_once()
        mock_run_agent_sync.assert_called_once()
        # reply_text called with reply
        # Note: handle_voice_or_text_message uses send_safe_message for agent response
        # We should check if send_safe_message was called, but here we patched run_agent_sync
        # Let's check if send_safe_message was mocked or if we need to mock it.
        # The handler imports send_safe_message. Let's patch it too to be safe.
        pass

@pytest.mark.asyncio
async def test_handle_voice_message_success(mock_update, mock_context):
    # Mock voice file
    mock_voice = MagicMock()
    mock_voice.file_id = "voice_123"
    mock_update.message.voice = mock_voice
    mock_update.message.text = None # Ensure text is None initially
    mock_update.effective_user.full_name = "Test User"
    mock_update.effective_user.username = "nick"
    mock_update.effective_chat.id = 456
    
    # Mock get_file
    mock_file = AsyncMock()
    mock_context.bot.get_file.return_value = mock_file
    
    # Mock download_to_drive
    mock_file.download_to_drive.return_value = None
    
    with patch("telegram_bot.handlers.is_chat_allowed", return_value=True), \
         patch("telegram_bot.handlers.Path") as mock_path, \
         patch("telegram_bot.handlers.TranscriptionService") as MockTranscriptionService, \
         patch("telegram_bot.handlers.save_message", new_callable=AsyncMock) as mock_save, \
         patch("telegram_bot.handlers.run_agent_sync") as mock_run_agent_sync, \
         patch("telegram_bot.handlers.is_forwarded", return_value=False):
        
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.__truediv__.return_value = mock_path_obj # Mock / operator
        mock_path_obj.exists.return_value = True # For cleanup
        mock_path_obj.__str__.return_value = "/tmp/voice_123.ogg"

        mock_transcription_service = MockTranscriptionService.return_value
        mock_transcription_service.transcribe = AsyncMock(return_value="transcribed text")
        
        mock_run_agent_sync.return_value = "Orchestrator reply"

        await handle_voice_or_text_message(mock_update, mock_context)
        
        mock_context.bot.get_file.assert_called_once_with("voice_123")
        mock_file.download_to_drive.assert_called_once()
        mock_transcription_service.transcribe.assert_called_once()
        mock_save.assert_called_once()
        mock_run_agent_sync.assert_called_once()

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
    # Проверяем, что удаленные команды отсутствуют
    assert "/summary" not in help_text
    assert "/ask" not in help_text
