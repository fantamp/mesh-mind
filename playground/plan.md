# Implementation Plan: Telegram -> ADK PoC

## Goal
Build a local, non-Docker proof-of-concept that ingests Telegram messages (text, audio, image) into a local SQLite database, and processes them using a Google ADK Agent (Gemini) for transcription, recognition, and analysis.

## User Review Required
> [!IMPORTANT]
> **API Keys Needed**: You will need a **Telegram Bot Token** (from @BotFather) and a **Google Gemini API Key** (from AI Studio).

## Proposed Changes

### 1. Environment Setup
#### [NEW] requirements.txt
- `python-telegram-bot`
- `google-adk`
- `google-generativeai`
- `pydantic`

### 2. Persistence Layer
#### [NEW] playground/db.py
- Function `init_db()`: Creates `messages` table with columns:
    - `id`, `chat_id`, `text`, `file_path`, `type`, `created_at`, `status` (PENDING, READY_FOR_SUMMARY, SUMMARIZED).
- Function `add_message(...)`: Inserts new message (Status: PENDING).
- Function `get_pending_messages()`: Retrieves `PENDING` messages (for Stage 1).
- Function `get_unsummarized_messages(chat_id)`: Retrieves `READY_FOR_SUMMARY` messages.
- Function `mark_ready_for_summary(msg_id, processed_text)`: Updates status after transcription/desc.
- Function `mark_summarized(chat_id)`: Marks all as `SUMMARIZED`.
- Function `get_last_message_time(chat_id)`: Returns timestamp of last message.

### 3. Telegram Bot (Producer)
#### [NEW] playground/bot.py
- Uses `python-telegram-bot`.
- Handlers for `TEXT`, `PHOTO`, `VOICE`.
- Downloads media to `playground/downloads/`.
- Calls `db.add_message()`.
- Runs with `app.run_polling()`.

### 4. ADK Agent (Consumer)
#### [NEW] playground/worker.py
- Uses `google-genai` (Gemini 2.0 Flash recommended for speed/multimodal).
- **Configuration**:
    - API Key from env.
    - System Prompt: "You are an intelligent assistant analyzing Telegram messages."
- **Processing Loop**:
    1. **Stage 1 (Normalization)**:
        - Fetch `PENDING` messages.
        - Transcribe Audio / Describe Images / Pass Text.
        - Update DB: `mark_ready_for_summary(id, final_text)`.
    2. **Stage 2 (Summarization)**:
        - Group `READY_FOR_SUMMARY` messages by `chat_id`.
        - Check Triggers:
            - If `last_message_text == '/summarize'` -> Trigger immediately.
            - If `time.now() - last_message_time > 60s` -> Trigger.
        - If Triggered:
            - Combine all texts.
            - Call `generate_content("Summarize: ...")`.
            - **Send to Telegram**: Use `bot.send_message(chat_id, summary)`.
            - Update DB: `mark_summarized(chat_id)`.
    3. Sleep 1s.

## Verification Plan

### Automated Tests
- None (PoC).

### Manual Verification
1.  **Start Bot**: `python playground/bot.py`
2.  **Start Worker**: `python playground/worker.py`
3.  **Send Text**: Send "Hello" to bot. Check `local_data.db` has the message. Check `worker` output logs "Processed".
4.  **Send Image**: Send a photo. Check `downloads/` folder. Check `worker` logs "Image recognized".
5.  **Send Voice**: Send a voice note (Ukrainian/Russian). Check `worker` logs transcription.
