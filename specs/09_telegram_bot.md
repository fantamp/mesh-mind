# Specification: Telegram Bot (telegram_bot)

## 1. Overview
This is a standalone Python application that interfaces with the Telegram Bot API. It handles user interactions and forwards data to the AI Core API.

## 2. Requirements

### 2.1. Framework
-   **Library:** `python-telegram-bot` (v20+ async) or `aiogram` (v3+). *Decision: `python-telegram-bot` is standard and robust.*
-   **Configuration:** Token from `.env`.

### 2.2. Message Handling
-   **Text Messages:**
    -   Send to `POST /ingest` (API).
-   **Voice Messages:**
    -   Download file locally.
    -   Send to `POST /ingest` (API) with `file` field.
-   **Images:**
    -   **Ignore** or reply "Images are not supported yet". *Decision: Ignore to avoid spamming the chat, or log debug message.*

### 2.3. Commands
-   `/start`: Welcome message.
-   `/summary`:
    -   Call `POST /summarize` (API).
    -   Send result to chat.
-   `/ask <question>`:
    -   Call `POST /ask` (API).
    -   Send result to chat.

### 2.4. Resilience
-   Long Polling mode.
-   Auto-reconnect on network failure.
-   Log errors but don't crash the main loop.

## 3. Implementation Details
-   Create `telegram_bot/main.py`.
-   Use `httpx` or `aiohttp` for making API calls to AI Core.

## 4. Verification & Definition of Done
-   [ ] Bot starts and connects to Telegram.
-   [ ] Text message is received and sent to API (verify via API logs).
-   [ ] Voice message is transcribed and text is saved (verify via DB).
-   [ ] `/summary` returns a response.
-   [ ] `/ask` returns a response.
-   [ ] **Manual Test:** Run the bot, send "Hello", check if it appears in SQLite `messages` table.
