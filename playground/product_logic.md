# Product Logic: Telegram Intelligent Summarizer PoC

## Core Value
An automated assistant that listens to a Telegram chat, understands all content (text, voice, images), and provides concise summaries of discussions when they finish.

## 1. Ingestion (The "Ears")
The bot is a silent listener in the chat. It captures everything:
*   **Text Messages**: Saved as-is.
*   **Voice Notes**: Automatically transcribed to text (supports Ukrainian, Russian, English).
*   **Images**: Automatically analyzed and described in text (e.g., "A screenshot of a code error", "A photo of a whiteboard diagram").

## 2. Normalization (The "Brain" - Stage 1)
As soon as a message arrives, it is "normalized" into a text format.
*   *User sends voice* -> *Bot sees text*: "[TRANSCRIPTION]: Привет, давайте обсудим..."
*   *User sends photo* -> *Bot sees text*: "[IMAGE]: A graph showing revenue growth..."

## 3. Summarization (The "Brain" - Stage 2)
The bot decides when to speak based on the conversation flow.

### Triggers
The bot will generate and send a summary in two cases:
1.  **Natural Pause**: The chat has been silent for **60 seconds** after a burst of messages.
2.  **Explicit Command**: A user types `/summarize` to force an immediate summary.

### The Output
The summary is sent back to the chat. It should:
*   Be concise.
*   Highlight key decisions or action items.
*   Capture the context of voice and images as well as text.
