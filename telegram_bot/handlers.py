import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import os
from datetime import datetime, timezone

from telegram_bot.utils import (
    is_chat_allowed, 
    extract_author_from_message, 
    is_forwarded
)
from ai_core.common.config import settings
from ai_core.storage.db import save_message
from ai_core.common.models import Message
from ai_core.common.transcription import TranscriptionService
from ai_core.agents.orchestrator.agent import root_agent as orchestrator
from ai_core.common.adk import run_agent_sync

logger = logging.getLogger(__name__)

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    is_allowed = is_chat_allowed(chat_id)
    status_icon = "✅ Authorized" if is_allowed else "❌ Not Authorized"
    
    msg = (
        rf"👋 Hello {user.mention_html()}! I'm Mesh Mind Bot."
        f"\n\nChat ID: <code>{chat_id}</code>"
        f"\nStatus: {status_icon}"
    )
    
    if not is_allowed:
        msg += "\n\nIf not authorized, please add this chat ID to TELEGRAM_ALLOWED_CHAT_IDS in your .env file."
    else:
        msg += "\n\nSend me text or voice messages, and I will save them."
        
    await update.message.reply_html(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать справку по командам бота."""
    if not is_chat_allowed(update.effective_chat.id):
        return
    
    chat_id = update.effective_chat.id
    
    help_text = f"""
🤖 **Mesh Mind Bot**

Ваш Chat ID: `{chat_id}`

**Что я умею:**
• 💾 **Сохраняю всё**: Текст и голосовые сообщения (транскрибирую их).
• 🗣️ **Понимаю обычный язык**: Просто напишите мне что-нибудь, и я отвечу (через оркестратора).

**Команды:**
• `/start` — Статус бота
• `/help` — Эта справка

**Для тестирования в ADK Web:**
Используйте формат: `Context: chat_id={chat_id} Question: ваш вопрос`
    """.strip()
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    text = update.message.text
    user = update.effective_user
    chat = update.effective_chat

    # Regular flow via orchestrator
    try:
        # 1. Save message
        msg = Message(
            source="telegram",
            chat_id=str(chat.id),
            author_id=str(user.id),
            author_name=user.full_name,
            author_nick=user.username,
            content=text,
            created_at=datetime.fromtimestamp(update.message.date.timestamp(), tz=timezone.utc)
        )
        await save_message(msg)

        # Check if forwarded
        if is_forwarded(update.message):
            if not settings.BOT_SILENT_MODE:
                await update.message.reply_text("Saved (forwarded message).")
            return

        # 2. Call Orchestrator
        # Use run_agent_sync to handle ADK runner complexity
        # Inject context
        context_text = f"Context: chat_id={chat.id}\nQuestion: {text}"
        
        reply_text = await asyncio.to_thread(
            run_agent_sync,
            agent=orchestrator,
            user_message=context_text,
            user_id=str(user.id),
            session_id=str(chat.id)
        )
        
        if reply_text:
            await update.message.reply_text(reply_text)
        elif not settings.BOT_SILENT_MODE:
            # Only send confirmation if not in silent mode and no reply from orchestrator
            await update.message.reply_text(f"Saved: {text[:20]}..." if len(text) > 20 else f"Saved: {text}")
            
    except Exception as e:
        logger.error(f"Error sending to orchestrator: {e}")
        if not settings.BOT_SILENT_MODE:
            await update.message.reply_text("Saved (error sending to orchestrator).")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    voice = update.message.voice
    file_id = voice.file_id
    new_file = await context.bot.get_file(file_id)
    
    # Create a temporary directory if it doesn't exist
    temp_dir = Path("temp_voice")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / f"{file_id}.ogg"
    
    await new_file.download_to_drive(file_path)
    
    user = update.effective_user
    chat = update.effective_chat
    author_id, author_nick, author_name = extract_author_from_message(update.message)
    
    try:
        # 1. Transcribe
        transcription_service = TranscriptionService()
        transcription = await transcription_service.transcribe(str(file_path))
        
        # 2. Save message
        msg = Message(
            source="telegram",
            chat_id=str(chat.id),
            author_id=author_id or str(user.id),
            author_name=author_name or user.full_name,
            author_nick=author_nick or user.username,
            content=transcription or "[Voice Message]",
            created_at=datetime.fromtimestamp(update.message.date.timestamp(), tz=timezone.utc),
            media_type="voice",
            media_path=str(file_path) # Note: file_path is local temp, ideally should be permanent storage
        )
        await save_message(msg)

        # 3. Send transcription to orchestrator
        if transcription:
            try:
                reply_text = await asyncio.to_thread(
                    run_agent_sync,
                    agent=orchestrator,
                    user_message=transcription,
                    user_id=str(user.id),
                    session_id=str(chat.id)
                )
                
                if reply_text:
                    await update.message.reply_text(reply_text)
                elif not settings.BOT_SILENT_MODE:
                     await update.message.reply_text("Voice message saved.")
            except Exception as e:
                logger.error(f"Error sending voice transcription to orchestrator: {e}")
                if not settings.BOT_SILENT_MODE:
                    await update.message.reply_text("Voice message saved (orchestrator error).")
        else:
            if not settings.BOT_SILENT_MODE:
                await update.message.reply_text("Voice message saved (no transcription).")
    except Exception as e:
        logger.error(f"Error saving voice: {e}")
        await update.message.reply_text("Failed to save voice message.")
    finally:
        # Clean up
        if file_path.exists():
            file_path.unlink()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
