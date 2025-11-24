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
TELEGRAM_ALLOWED_CHAT_IDS = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in TELEGRAM_ALLOWED_CHAT_IDS.split(",") if cid.strip()]

def is_chat_allowed(chat_id: int) -> bool:
    """Check if the chat ID is allowed."""
    if not ALLOWED_CHAT_IDS:
        return True # Allow all if whitelist is empty
    return chat_id in ALLOWED_CHAT_IDS

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
    async def summarize(self, chat_id: int, **kwargs):
        """Calls the summarize endpoint."""
        url = f"{self.base_url}/summarize"
        payload = {"chat_id": chat_id, **kwargs}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ask(self, question: str, chat_id: int):
        """Calls the ask endpoint."""
        url = f"{self.base_url}/ask"
        payload = {"query": question, "chat_id": str(chat_id)}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()

# Initialize API Client
api_client = ApiClient(AI_CORE_API_URL)

def parse_summary_params(args: list) -> dict:
    """
    Парсит параметры команды /summary.
    
    Args:
        args: Список аргументов команды
        
    Returns:
        Словарь с параметрами: {"mode": "auto|count|time", "value": ...}
    """
    if not args:
        # Дефолтное поведение - автоопределение разговора
        return {"mode": "auto"}
    
    param = args[0].strip()
    
    # Проверка на число (количество сообщений)
    if param.isdigit():
        return {"mode": "count", "value": int(param)}
    
    # Проверка на формат времени (2h, 30m)
    if len(param) > 1:
        number_part = param[:-1]
        unit = param[-1].lower()
        
        if number_part.isdigit():
            if unit == 'h':
                return {"mode": "time", "hours": int(number_part)}
            elif unit == 'm':
                return {"mode": "time", "minutes": int(number_part)}
    
    # Если не удалось распарсить, используем auto режим
    return {"mode": "auto"}


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
        msg += "\n\nSend me text or voice messages, and I will save them. Use /summary or /ask to interact."
        
    await update.message.reply_html(msg)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger summarization с поддержкой различных параметров и reply."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    chat_id = update.effective_chat.id
    
    await update.message.reply_text("Generating summary, please wait...")
    
    try:
        # Подготовка параметров для API
        api_params = {"chat_id": chat_id}
        
        # ПРИОРИТЕТ 1: Проверка на reply - имеет наивысший приоритет
        if update.message.reply_to_message:
            # Пользователь сделал reply на сообщение
            # Используем timestamp этого сообщения как начало периода
            reply_msg = update.message.reply_to_message
            since_dt = reply_msg.date  # Telegram API возвращает datetime в UTC
            
            api_params["since_datetime"] = since_dt.isoformat()
            api_params["limit"] = 1000  # Большой лимит для временного интервала
            
        # ПРИОРИТЕТ 2: Парсинг параметров команды (только если нет reply)
        else:
            params = parse_summary_params(context.args if context.args else [])
            
            if params["mode"] == "count":
                # Указано количество сообщений
                api_params["limit"] = params["value"]
                
            elif params["mode"] == "time":
                # Указан временной интервал
                from datetime import datetime, timedelta, timezone
                
                now = datetime.now(timezone.utc)
                if "hours" in params:
                    since = now - timedelta(hours=params["hours"])
                else:  # minutes
                    since = now - timedelta(minutes=params["minutes"])
                
                api_params["since_datetime"] = since.isoformat()
                api_params["limit"] = 1000  # Большой лимит для временного интервала
            
            # Если mode="auto" (дефолт), мы просто не передаем since_datetime и limit (или дефолтный limit)
            # API само разберется (возьмет от последнего саммари)
        
        # Вызов API
        result = await api_client.summarize(**api_params)
        summary_text = result.get("summary", "No summary available.")
        await update.message.reply_text(summary_text)
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        await update.message.reply_text("Sorry, I couldn't get the summary at this time.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать справку по командам бота."""
    if not is_chat_allowed(update.effective_chat.id):
        return
    
    help_text = """
📚 **Mesh Mind Bot - Commands**

**Basic Commands:**
• `/start` - Welcome message and chat status
• `/help` - Show this help message

**Summary Commands:**
• `/summary` - Auto-detect and summarize the latest conversation (based on message gaps)
• `/summary` (reply) - **Reply to any message** and use `/summary` to get summary from that message
• `/summary N` - Summarize last N messages (e.g., `/summary 20`)
• `/summary Nh` - Summarize messages from last N hours (e.g., `/summary 2h`)
• `/summary Nm` - Summarize messages from last N minutes (e.g., `/summary 30m`)

**Q&A Command:**
• `/ask <question>` - Ask a question based on the knowledge base

**Message Processing:**
I automatically save all text and voice messages you send to the chat for future reference.
    """.strip()
    
    await update.message.reply_text(help_text, parse_mode="Markdown")




async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask a question."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    if not context.args:
        await update.message.reply_text("Please provide a question: /ask <your question>")
        return

    question = " ".join(context.args)
    await update.message.reply_text(f"Thinking about: '{question}'...")
    try:
        result = await api_client.ask(question, chat_id=update.effective_chat.id)
        answer = result.get("answer", "I don't know the answer.")
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        await update.message.reply_text("Sorry, I couldn't answer your question at this time.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    if not is_chat_allowed(update.effective_chat.id):
        return

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
    application.add_handler(CommandHandler("help", help_command))
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
