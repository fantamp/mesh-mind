# Specification: Transcription Service (ai_core/common)

## 1. Overview
This service handles the conversion of voice messages to text using Google Gemini's multimodal capabilities.

## 2. Requirements

### 2.1. Core Logic
-   **Model:** Use `Settings.GEMINI_MODEL_FAST` (e.g., `gemini-2.5-flash`).
-   **Input:** Path to a local audio file (OGG, MP3, WAV).
-   **Output:** Transcribed text string.

### 2.2. Language Support
-   **Requirement:** Must support **Ukrainian**, **Russian**, and **English**.
-   **Implementation:** Gemini Multimodal handles language detection automatically, but we should verify this in the prompt or configuration if needed.
-   **Prompting:** When calling Gemini with the audio file, include a system prompt: *"Transcribe this audio. It may be in Ukrainian, Russian, or English. Output only the transcription."*

### 2.3. Implementation (`transcription.py`)
-   **Class:** `TranscriptionService`
-   **Method:** `async def transcribe(audio_path: str) -> str`
-   **Steps:**
    1.  Upload file to Gemini File API (`genai.upload_file`).
    2.  Wait for processing (usually instant for small files).
    3.  Generate content using the model with the file and the prompt.
    4.  **Cleanup:** Delete the file from Gemini Cloud storage after transcription (`genai.delete_file`) to avoid clutter/costs.

## 3. Implementation Details
-   Handle `google.api_core.exceptions` (network, quota).
-   **Resilience:** Use `@retry` decorator from `tenacity` library to handle transient API errors.
-   Ensure the local file exists before uploading.

## 4. Verification & Definition of Done
-   [ ] `transcribe()` method works with a sample OGG file.
-   [ ] Correctly transcribes a mixed UA/RU/EN sentence.
-   [ ] File is uploaded to Gemini and then deleted (verify via log or API check if possible, or just ensure delete code runs).
-   [ ] **Manual Test:** Run `tests/manual/test_transcribe.py` with a sample voice note.
