import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import os
import html
from datetime import datetime, timezone

from telegram_bot.utils import (
    is_chat_allowed, 
    extract_author_from_message, 
    is_forwarded,
    send_safe_message
)

from ai_core.common.config import settings
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


async def extract_text_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> (str, str):
    """Extracts text content and its media type from an incoming message.

    Args:
        update (Update): The Telegram Update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the bot instance.

    Returns:
        tuple[str, str]: A tuple containing the extracted text and its media type ("text" or "voice").

    Raises:
        Exception: If the message type is unknown or transcription fails for a voice message.
    """
    if update.message.voice:
        voice = update.message.voice
        file_id = voice.file_id
        new_file = await context.bot.get_file(file_id)
        
        # Create a temporary directory if it doesn't exist
        temp_dir = Path("tmp")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / f"{file_id}.ogg" # FIXME: dangerously using file_id as filename
        
        try:
            await new_file.download_to_drive(file_path)
        
            transcription_service = TranscriptionService()
            transcription = await transcription_service.transcribe(str(file_path))

            if not transcription:
                raise Exception("empty transcription returned from the transcription service")
        finally:
            if file_path.exists():
                file_path.unlink()

        return transcription, "voice"
    elif update.message.text:
        return update.message.text, "text"
    raise Exception("unknown message type")


async def handle_voice_or_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages."""
    if not is_chat_allowed(update.effective_chat.id):
        logger.info(f"Message from disallowed chat: {update.effective_chat.id}")
        return
    
    text, media_type = await extract_text_from_message(update, context)
    user = update.effective_user
    chat = update.effective_chat
    
    # Extract Content Author (original author if forward, else current user)
    author_id, author_nick, author_name = extract_author_from_message(update.message)
    is_fwd = is_forwarded(update.message)

    is_message_saved = False
    agent_response = None
    reply = []
    
    try:
        # Get or create canvas
        from ai_core.services.canvas_service import canvas_service
        canvas = await canvas_service.get_or_create_canvas_for_chat(str(chat.id))
        
        # Prepare attributes
        attrs = {
            "source": "telegram",
            "source_msg_id": str(update.message.message_id),
            "author_name": author_name,
            "author_nick": author_nick,
        }
        
        if author_id:
            attrs["author_id"] = author_id
            
        if is_fwd:
            attrs["is_forward"] = 1
        
        # Save to canvas
        # created_by is ALWAYS the user who sent/forwarded the message to the bot
        # Format: telegram:{id} | {username} | {full_name}
        parts = [f"telegram:{user.id}", user.username, user.full_name]
        creator_str = " | ".join([p for p in parts if p])
        
        await canvas_service.add_element(
            canvas_id=canvas.id,
            type=media_type, # "text" or "voice"
            content=text,
            created_by=creator_str,
            attributes=attrs
        )
        is_message_saved = True

        MAX_TRANSCRIPTION_PREVIEW_LENGTH = 140
        if media_type == "voice":
            escaped_text = html.escape(text)
            preview_text = escaped_text[:MAX_TRANSCRIPTION_PREVIEW_LENGTH] + "..." if len(escaped_text) > MAX_TRANSCRIPTION_PREVIEW_LENGTH else escaped_text
            reply.append(f"<blockquote><i>{preview_text}</i></blockquote>")

        ctx = attrs.copy()
        ctx["media_type"] = media_type
        ctx["added_by"] = creator_str
        ctx_str = '\n'.join([f'{k}: {v}' for k, v in ctx.items()])
        contexted_text = f"{ctx_str}\n\nMessage:\n\n{text}"
        agent_response = await asyncio.to_thread(
            run_agent_sync,
            agent=orchestrator,
            user_message=contexted_text,
            user_id=str(user.id),
            chat_id=str(chat.id)
        )
        
    except Exception as e:
        logger.error(f"Got an error: {e}")
        reply.append(f"Got an error during processing: {html.escape(str(e))}")
    finally:        
        if not agent_response and is_message_saved and not settings.BOT_SILENT_MODE:
            reply.append("Message saved.")

        if reply:
            # Join with newlines, but since blockquote is a block element, it handles its own spacing mostly.
            # However, for HTML parse mode, we just concatenate.
            await update.message.reply_text("\n".join(reply), parse_mode="HTML")
        if agent_response:
            await send_safe_message(update, agent_response)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
