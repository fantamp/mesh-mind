import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from telegram_bot.handlers import (
    start_command,
    help_command,
    handle_voice_or_text_message,
    error_handler
)
from telegram_bot.utils import ALLOWED_CHAT_IDS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def post_init(application: Application) -> None:
    """Notify admins that the bot has started."""
    if not ALLOWED_CHAT_IDS:
        return
    
    msg = "🤖 **System Notification**\n\nBot has successfully (re)started and is ready to serve."
    
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await application.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to send startup message to {chat_id}: {e}")

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return

    # Build Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT | filters.VOICE & ~filters.COMMAND, handle_voice_or_text_message))

    # Errors
    application.add_error_handler(error_handler)

    # Run the bot
    logger.info("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
