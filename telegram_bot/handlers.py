import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone, timedelta

from telegram_bot.utils import (
    is_chat_allowed, 
    extract_author_from_message, 
    is_forwarded, 
    parse_summary_params
)
from telegram_bot.api_client import ApiClient

logger = logging.getLogger(__name__)

# --- Helper for accessing ApiClient ---
def get_api_client(context: ContextTypes.DEFAULT_TYPE) -> ApiClient:
    return context.bot_data["api_client"]

# --- Forward Handling Logic ---

async def forward_summary_job(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Summarize accumulated forwarded messages after debounce."""
    # State is stored in chat_data
    # Structure: context.chat_data["forward_pool"] = {"messages": [], "first_time": datetime}
    
    state = context.chat_data.get("forward_pool")
    if not state or not state.get("messages"):
        return

    first_time: datetime = state["first_time"]
    limit = len(state["messages"]) + 5  # небольшой запас

    api_client = get_api_client(context)

    try:
        # Notify start
        await context.bot.send_message(chat_id=chat_id, text="Ну штош... запускаю суммаризацию...")

        resp = await api_client.summarize(
            chat_id=chat_id,
            since_datetime=first_time.isoformat(),
            limit=limit
        )
        summary_text = resp.get("summary", "No summary available.")
        if not summary_text or summary_text == "No new messages to summarize.":
            summary_text = "Саммари нет."
        await context.bot.send_message(chat_id=chat_id, text=summary_text)
    except Exception as e:
        logger.error(f"Forward summary failed: {e}")
    finally:
        # Clear state
        context.chat_data.pop("forward_pool", None)
        # Task cleanup is handled by the fact that this coroutine finishes

def schedule_forward_summary(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Debounce scheduler."""
    # Cancel existing task if any
    existing_task = context.chat_data.get("forward_task")
    if existing_task and not existing_task.done():
        existing_task.cancel()
        
    async def runner():
        await asyncio.sleep(5)
        await forward_summary_job(chat_id, context)
        
    task = asyncio.create_task(runner())
    context.chat_data["forward_task"] = task

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
        msg += "\n\nSend me text or voice messages, and I will save them. Use /summary or /ask to interact."
        
    await update.message.reply_html(msg)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger summarization с поддержкой различных параметров и reply."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    chat_id = update.effective_chat.id
    api_client = get_api_client(context)
    
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
                now = datetime.now(timezone.utc)
                if "hours" in params:
                    since = now - timedelta(hours=params["hours"])
                else:  # minutes
                    since = now - timedelta(minutes=params["minutes"])
                
                api_params["since_datetime"] = since.isoformat()
                api_params["limit"] = 1000  # Большой лимит для временного интервала
            
            # Если mode="auto" (дефолт), мы просто не передаем since_datetime и limit
        
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
    
    chat_id = update.effective_chat.id
    
    help_text = f"""
🤖 **Mesh Mind Bot**

Ваш Chat ID: `{chat_id}`

💡 **Как тестировать оркестратор:**
Если вы хотите проверить работу агента с контекстом этого чата, используйте такой формат запроса:
`CONTEXT: chat_id={chat_id} Question: Суммаризируй последние 10 сообщений`

---
**Что я умею:**
• 💾 **Сохраняю всё**: Текст и голосовые сообщения (транскрибирую их).
• 🗣️ **Понимаю обычный язык**: Просто напишите "Суммаризируй чат", "О чем говорили?" или задайте вопрос.
• 🔄 **Работаю с пересылкой**: Перешлите мне сообщения, и я сделаю их саммари (через 5 сек).

**Команды:**
• `/start` — Статус бота
• `/help` — Эта справка
• `/summary` — Авто-саммари (по паузам)
• `/summary 20` — Саммари последних 20 сообщений
• `/summary 2h` — Саммари за последние 2 часа
• `/summary 2m` — Саммари за последние 2 минуты
• `/ask <вопрос>` — Вопрос к базе знаний
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
    api_client = get_api_client(context)

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
    author_id, author_nick, author_name = extract_author_from_message(update.message)
    api_client = get_api_client(context)

    # --- Forward / Mixed Content Handling ---
    
    # Check if we are already in a "waiting for forwards" state
    state = context.chat_data.get("forward_pool")
    
    if state:
        # We are in the waiting window.
        # ANY message (text or forward) is added to the pool and orchestrator is SKIPPED.
        state["messages"].append(update.message)
        context.chat_data["forward_pool"] = state
        
        # Reset the timer (debounce)
        schedule_forward_summary(chat.id, context)
        
        # Save the message (ingest only, no orchestrator)
        try:
            await api_client.ingest_text(
                text,
                author_name=author_name or user.full_name,
                author_id=author_id or str(user.id),
                author_nick=author_nick or user.username,
                chat_id=str(chat.id)
            )
        except Exception as e:
            logger.error(f"Error saving mixed content text: {e}")
            
        return  # SKIP ORCHESTRATOR

    # If not in waiting state, check if this is a new forward chain
    if is_forwarded(update.message):
        # Start new pool
        state = {"messages": [update.message], "first_time": update.message.date, "warning_sent": True}
        context.chat_data["forward_pool"] = state
        
        # Send the warning message ONCE
        await update.message.reply_text(
            "Я жду ещё пять секунд доп. сообщения и на это время отключил оркестратора. "
            "Если ничего не пришлете, то отправлю присланный пул сообщений в суммаризатор."
        )
        
        schedule_forward_summary(chat.id, context)
        
        # Ingest forward
        try:
            await api_client.ingest_text(
                text,
                author_name=author_name or user.full_name,
                author_id=author_id or str(user.id),
                author_nick=author_nick or user.username,
                chat_id=str(chat.id)
            )
        except Exception as e:
            logger.error(f"Error saving forwarded text: {e}")
        return

    # Non-forward & No active pool: regular flow via orchestrator
    try:
        resp = await api_client.chat_message({
            "chat_id": str(chat.id),
            "user_id": str(user.id),
            "user_name": user.full_name,
            "user_nick": user.username,
            "text": text,
            "message_id": str(update.message.message_id),
            "reply_to_message_id": str(update.message.reply_to_message.message_id) if update.message.reply_to_message else None,
            "skip_save": False
        })
        if not isinstance(resp, dict):
            resp = {}
        reply_text = resp.get("reply")
        if reply_text:
            await update.message.reply_text(reply_text)
        else:
            await update.message.reply_text("Saved.")
    except Exception as e:
        logger.error(f"Error sending to orchestrator: {e}")
        await update.message.reply_text("Saved.")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages."""
    if not is_chat_allowed(update.effective_chat.id):
        return

    voice = update.message.voice
    file_id = voice.file_id
    new_file = await context.bot.get_file(file_id)
    api_client = get_api_client(context)
    
    # Create a temporary directory if it doesn't exist
    temp_dir = Path("temp_voice")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / f"{file_id}.ogg"
    
    await new_file.download_to_drive(file_path)
    
    user = update.effective_user
    chat = update.effective_chat
    author_id, author_nick, author_name = extract_author_from_message(update.message)
    
    try:
        resp = await api_client.ingest_file(
            str(file_path),
            author_name=author_name or user.full_name,
            author_id=author_id or str(user.id),
            author_nick=author_nick or user.username,
            chat_id=str(chat.id)
        )
        if not isinstance(resp, dict):
            resp = {}
        transcription = resp.get("text")

        # --- Forward / Mixed Content Handling (Voice) ---
        
        # Check if we are already in a "waiting for forwards" state
        state = context.chat_data.get("forward_pool")
        
        if state:
            # We are in the waiting window.
            # Add to pool and SKIP ORCHESTRATOR.
            state["messages"].append(update.message)
            context.chat_data["forward_pool"] = state
            
            # Reset the timer
            schedule_forward_summary(chat.id, context)
            return

        # If not in waiting state, check if this is a new forward chain
        if is_forwarded(update.message):
            # Start new pool
            state = {"messages": [update.message], "first_time": update.message.date, "warning_sent": True}
            context.chat_data["forward_pool"] = state
            
            # Send the warning message ONCE
            await update.message.reply_text(
                "Я жду ещё пять секунд доп. сообщения и на это время отключил оркестратора. "
                "Если ничего не пришлете, то отправлю присланный пул сообщений в суммаризатор."
            )
            
            schedule_forward_summary(chat.id, context)
            return

        # Non-forward voice & No active pool: send transcription to orchestrator
        if transcription:
            try:
                resp_chat = await api_client.chat_message({
                    "chat_id": str(chat.id),
                    "user_id": str(user.id),
                    "user_name": user.full_name,
                    "user_nick": user.username,
                    "text": transcription,
                    "message_id": str(update.message.message_id),
                    "reply_to_message_id": str(update.message.reply_to_message.message_id) if update.message.reply_to_message else None,
                    "skip_save": True  # уже сохранили голос; не дублируем текст
                })
                reply_text = resp_chat.get("reply")
                if reply_text:
                    await update.message.reply_text(reply_text)
                else:
                    await update.message.reply_text("Voice message saved and processing.")
            except Exception as e:
                logger.error(f"Error sending voice transcription to orchestrator: {e}")
                await update.message.reply_text("Voice message saved and processing.")
        else:
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
