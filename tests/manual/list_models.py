import google.generativeai as genai
import os
import sys

# Add project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from ai_core.common.config import settings

def list_models():
    if not settings.GOOGLE_API_KEY:
        print("GOOGLE_API_KEY is not set.")
        return

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

if __name__ == "__main__":
    list_models()
