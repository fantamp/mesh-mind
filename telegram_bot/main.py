import os
import logging
from dotenv import load_dotenv

# Load environment variables first, before importing modules that rely on them
load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from telegram_bot.handlers import (
    start_command,
    help_command,
    handle_voice_or_text_message,
    error_handler
)
import asyncio
from telegram_bot.utils import ALLOWED_CHAT_IDS
from telegram_bot.monitor import CommitMonitor

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def monitor_loop(application: Application):
    """Background task to check for new commits every 15 minutes.
    
    See docs/features/new-commit-notify.md for more details.
    """
    monitor = CommitMonitor()
    
    while True:
        try:
            # Wait 15 minutes
            await asyncio.sleep(5 * 60)
            
            logger.info("Checking for new commits...")
            new_commits = await asyncio.to_thread(monitor.check_for_updates)
            
            if new_commits:
                msg = "🚀 **New Commits Detected!**\n\n" + "\n".join(new_commits)
                msg += "\n\n_Use 'Update the bot' to pull changes._"
                
                for chat_id in ALLOWED_CHAT_IDS:
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                    except Exception as e:
                        logger.warning(f"Failed to send commit notification to {chat_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(60) # Wait a bit before retrying on error

async def send_startup_notification(application: Application):
    """Sends startup notification after a short delay."""
    await asyncio.sleep(5) # Wait for bot to fully initialize
    
    if not ALLOWED_CHAT_IDS:
        return
    
    msg = "🤖 *System Notification*\n\nBot has successfully (re)started and is ready to serve."
    
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await application.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to send startup message to {chat_id}: {e}")

async def post_init(application: Application) -> None:
    """Notify admins that the bot has started and start background tasks."""
    # Start the monitor loop
    asyncio.create_task(monitor_loop(application))
    # Start notification task
    asyncio.create_task(send_startup_notification(application))

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

    # Run DB Migration
    from ai_core.storage.db import init_db
    from ai_core.storage.migration import run_migration
    
    # Initialize DB (creates new tables)
    asyncio.run(init_db())
    
    # Run migration (moves data from old tables if present)
    asyncio.run(run_migration())

    # Run the bot
    logger.info("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
