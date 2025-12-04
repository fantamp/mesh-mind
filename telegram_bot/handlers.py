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
        await update.message.reply_text("Transcribing voice message...", reply_to_message_id=update.message.message_id)

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


async def process_message_content(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    media_type: str, 
    content: str, 
    attributes: dict,
    element_creator: callable
) -> None:
    """Shared logic for processing message content (text, voice, photo)."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Extract Content Author
    author_id, author_nick, author_name = extract_author_from_message(update.message)
    is_fwd = is_forwarded(update.message)
    
    # Prepare attributes
    attrs = {
        "source": "telegram",
        "source_msg_id": str(update.message.message_id),
        "author_name": author_name,
        "author_nick": author_nick,
        **attributes
    }
    
    if author_id:
        attrs["author_id"] = author_id
        
    if is_fwd:
        attrs["is_forward"] = 1
        
    # Creator string
    parts = [f"telegram:{user.id}", user.username, user.full_name]
    creator_str = " | ".join([p for p in parts if p])
    
    # Get canvas
    from ai_core.services.canvas_service import canvas_service
    canvas = await canvas_service.get_or_create_canvas_for_chat(str(chat.id))
    
    # Create Element
    try:
        element = await element_creator(
            canvas_id=canvas.id,
            created_by=creator_str,
            attributes=attrs
        )
        # Reply logic
        reply = []
        if media_type == "voice":
            escaped_text = html.escape(content)
            MAX_TRANSCRIPTION_PREVIEW_LENGTH = 140
            preview_text = escaped_text[:MAX_TRANSCRIPTION_PREVIEW_LENGTH] + "..." if len(escaped_text) > MAX_TRANSCRIPTION_PREVIEW_LENGTH else escaped_text
            reply.append(f"<blockquote><i>{preview_text}</i></blockquote>")
        elif media_type == "image":
            snippet = element.content[:200] + "..." if len(element.content) > 200 else element.content
            reply.append(f"🖼 <b>Image Saved</b>\n\n{html.escape(snippet)}")
            
        if reply:
            await update.message.reply_html("\n".join(reply), reply_to_message_id=update.message.message_id)
        
        # Trigger Agent
        ctx = element.attributes.copy()
        ctx["media_type"] = media_type
        ctx["added_by"] = creator_str
        ctx_str = '\n'.join([f'{k}: {v}' for k, v in ctx.items()])
        contexted_text = f"{ctx_str}\n\nMessage/Description:\n\n{element.content}"
        
        agent_response = await asyncio.to_thread(
            run_agent_sync,
            agent=orchestrator,
            user_message=contexted_text,
            user_id=str(user.id),
            chat_id=str(chat.id)
        )
                    
        if agent_response:
            await send_safe_message(update, agent_response)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(f"Error: {e}")


async def handle_voice_or_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice or text messages."""
    if not is_chat_allowed(update.effective_chat.id):
        return
    
    text, media_type = await extract_text_from_message(update, context)
    
    from ai_core.services.canvas_service import canvas_service
    
    async def create_text_element(canvas_id, created_by, attributes):
        return await canvas_service.add_element(
            canvas_id=canvas_id,
            type=media_type,
            content=text,
            created_by=created_by,
            attributes=attributes
        )
        
    await process_message_content(
        update, context, media_type, text, {}, create_text_element
    )


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos and image documents."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    # Get file
    if update.message.photo:
        file_obj = await update.message.photo[-1].get_file()
        file_name = f"photo_{file_obj.file_unique_id}.jpg"
    elif update.message.document:
        file_obj = await update.message.document.get_file()
        file_name = update.message.document.file_name or f"doc_{file_obj.file_unique_id}"
    else:
        return

    await update.message.reply_text("Processing image...", reply_to_message_id=update.message.message_id)

    file_data = await file_obj.download_as_bytearray()
    
    from ai_core.services.image_service import image_service
    
    async def create_image_element(canvas_id, created_by, attributes):
        return await image_service.process_image(
            file_data=bytes(file_data),
            original_filename=file_name,
            created_by=created_by,
            canvas_id=canvas_id
        )
        
    await process_message_content(
        update, context, "image", "", {}, create_image_element
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
