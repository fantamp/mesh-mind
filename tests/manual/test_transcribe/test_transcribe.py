import asyncio
import os
import sys
from loguru import logger

# Add project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ai_core.common.transcription import TranscriptionService

async def main():
    if len(sys.argv) < 2:
        print("No file provided. Running on default samples...")
        samples_dir = os.path.join(os.path.dirname(__file__), "samples")
        if not os.path.exists(samples_dir):
             print(f"Samples directory not found: {samples_dir}")
             sys.exit(1)
        
        files = [f for f in os.listdir(samples_dir) if f.endswith(('.m4a', '.ogg', '.mp3', '.wav'))]
        if not files:
            print("No audio samples found.")
            sys.exit(1)
            
        service = TranscriptionService()
        
        for file in files:
            audio_path = os.path.join(samples_dir, file)
            print(f"\nTesting transcription for: {file}")
            try:
                text = await service.transcribe(audio_path)
                print(f"--- Result ({file}) ---")
                print(text)
                print("----------------------------")
            except Exception as e:
                logger.error(f"Transcription failed for {file}: {e}")
        return

    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"Error: File not found at {audio_path}")
        sys.exit(1)

    print(f"Testing transcription for: {audio_path}")
    
    service = TranscriptionService()
    
    try:
        text = await service.transcribe(audio_path)
        print("\n--- Transcription Result ---")
        print(text)
        print("----------------------------\n")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
