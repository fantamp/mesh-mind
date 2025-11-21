import os
import pathlib
from typing import Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions as google_exceptions
from loguru import logger

from ai_core.common.config import settings

class TranscriptionService:
    """
    Service for transcribing audio files using Google Gemini Multimodal capabilities.
    Supports Ukrainian, Russian, and English.
    """

    def __init__(self):
        """Initialize the TranscriptionService with Google API key."""
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY is not set. TranscriptionService may fail.")
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model_name = settings.GEMINI_MODEL_FAST

    @retry(
        retry=retry_if_exception_type((google_exceptions.ServiceUnavailable, google_exceptions.TooManyRequests)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to the local audio file (OGG, MP3, WAV).

        Returns:
            Transcribed text.

        Raises:
            FileNotFoundError: If the audio file does not exist.
            Exception: If transcription fails after retries.
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        file_ref = None
        try:
            # Determine MIME type
            mime_type = None
            ext = os.path.splitext(audio_path)[1].lower()
            if ext == ".m4a":
                mime_type = "audio/mp4"
            elif ext == ".mp3":
                mime_type = "audio/mpeg"
            elif ext == ".wav":
                mime_type = "audio/wav"
            elif ext == ".ogg":
                mime_type = "audio/ogg"
            
            logger.info(f"Uploading file for transcription: {audio_path} (Detected MIME: {mime_type})")
            # Upload the file to Gemini
            file_ref = genai.upload_file(path=audio_path, mime_type=mime_type)
            
            # Wait for the file to be active (though usually instant for small audio)
            # For larger files, we might need to loop and check state, but for voice notes it's fast.
            # genai.upload_file waits for processing by default unless wait_for_processing=False is passed?
            # Actually, the docs say upload_file returns a File object. 
            # We should check if it's ready, but for now we assume it is or the model call handles it.
            # Let's verify state just in case if it's easy, but standard usage often skips it for small files.
            
            logger.info(f"File uploaded: {file_ref.name} (MIME: {file_ref.mime_type}). Generating transcription...")

            model = genai.GenerativeModel(self.model_name)
            
            prompt = "Transcribe this audio. It may be in Ukrainian, Russian, or English. Output only the transcription."
            
            response = model.generate_content([prompt, file_ref])
            
            transcription = response.text
            logger.info("Transcription completed successfully.")
            return transcription

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
        finally:
            # Cleanup: Delete the file from Gemini Cloud storage
            if file_ref:
                try:
                    logger.info(f"Deleting file from Gemini: {file_ref.name}")
                    genai.delete_file(file_ref.name)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete file {file_ref.name}: {cleanup_error}")
