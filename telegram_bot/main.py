import os
import json
import logging
import asyncio
from typing import Optional
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_CORE_API_URL = os.getenv("AI_CORE_API_URL", "http://localhost:8000/api")

class ApiClient:
    """Client for interacting with the AI Core API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ingest_text(self, text: str, source: str = "telegram", **kwargs):
        """Sends text to the ingestion endpoint."""
        url = f"{self.base_url}/ingest"
        
        # API expects multipart/form-data with 'metadata' as JSON string
        metadata = {"source": source, "type": "text", **kwargs}
        data = {
            "text": text,
            "metadata": json.dumps(metadata)
        }
        
        # httpx handles multipart/form-data when 'data' is used
        response = await self.client.post(url, data=data)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ingest_file(self, file_path: str, source: str = "telegram", **kwargs):
        """Sends a file to the ingestion endpoint."""
        url = f"{self.base_url}/ingest"
        
        metadata = {"source": source, "type": "file", **kwargs}
        data = {
            "metadata": json.dumps(metadata)
        }
        
        # Open the file in binary mode
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            response = await self.client.post(url, data=data, files=files)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def summarize(self, chat_id: int):
        """Calls the summarize endpoint."""
        url = f"{self.base_url}/summarize"
        payload = {"chat_id": chat_id}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ask(self, question: str):
        """Calls the ask endpoint."""
        url = f"{self.base_url}/ask"
        payload = {"query": question}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()

# Initialize API Client
api_client = ApiClient(AI_CORE_API_URL)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am your AI assistant. Send me text or voice messages, and I will save them. Use /summary or /ask to interact."
    )

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger summarization."""
    await update.message.reply_text("Generating summary, please wait...")
    try:
        result = await api_client.summarize(chat_id=update.effective_chat.id)
        summary_text = result.get("summary", "No summary available.")
        await update.message.reply_text(summary_text)
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        await update.message.reply_text("Sorry, I couldn't get the summary at this time.")

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask a question."""
    if not context.args:
        await update.message.reply_text("Please provide a question: /ask <your question>")
        return

    question = " ".join(context.args)
    await update.message.reply_text(f"Thinking about: '{question}'...")
    try:
        result = await api_client.ask(question)
        answer = result.get("answer", "I don't know the answer.")
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        await update.message.reply_text("Sorry, I couldn't answer your question at this time.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    text = update.message.text
    user = update.effective_user
    chat = update.effective_chat
    
    try:
        await api_client.ingest_text(
            text, 
            author_name=user.full_name, 
            author_id=str(user.id),
            chat_id=str(chat.id)
        )
        await update.message.reply_text("Saved.")
    except Exception as e:
        logger.error(f"Error saving text: {e}")
        await update.message.reply_text("Failed to save message.")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages."""
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

    try:
        await api_client.ingest_file(
            str(file_path),
            author_name=user.full_name,
            author_id=str(user.id),
            chat_id=str(chat.id)
        )
        await update.message.reply_text("Voice message saved and processing.")
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

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("ask", ask_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    # Errors
    application.add_error_handler(error_handler)

    # Run the bot
    logger.info("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
