import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from telegram_bot.api_client import ApiClient
from telegram_bot.handlers import (
    start_command,
    summary_command,
    help_command,
    ask_command,
    handle_text_message,
    handle_voice_message,
    error_handler
)

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

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return

    # Initialize API Client
    api_client = ApiClient(AI_CORE_API_URL)

    # Build Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Store dependencies in bot_data
    application.bot_data["api_client"] = api_client

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
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        # Cleanup
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(api_client.close())
        else:
            loop.run_until_complete(api_client.close())

if __name__ == "__main__":
    main()
