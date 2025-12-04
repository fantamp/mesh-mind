import pytest
import uuid
import os
from pathlib import Path
from ai_core.services.image_service import image_service
from ai_core.services.canvas_service import canvas_service
from ai_core.common.config import settings
from ai_core.storage.db import init_db

import base64

# Skip if no API key
@pytest.mark.skipif(not settings.GOOGLE_API_KEY, reason="GOOGLE_API_KEY not set")
@pytest.mark.asyncio
async def test_integration_gemini_vision():
    """Real call to Gemini Vision API."""
    # Force use of a known stable model
    settings.GEMINI_MODEL_FAST = "gemini-1.5-flash"
    
    # Create a dummy image (1x1 pixel white PNG)
    dummy_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAABgADNjd8qAAAAABJRU5ErkJggg==")
    

    # надо тестировать на реальном крупном файле-картинке. Я пока что положил в корень проекта 2025-12-04 20.02.18.jpg, забери оттуда и переложи в более правильное место 

    temp_path = await image_service.save_temp_image(dummy_png, "test_pixel.png")
    try:
        description = await image_service.generate_description(temp_path)
        assert description is not None
        assert len(description) > 0
        print(f"Gemini Description: {description}")
    finally:
        if temp_path.exists():
            os.remove(temp_path)

@pytest.mark.asyncio
async def test_e2e_full_pipeline():
    """Full pipeline: Save -> Describe -> Store -> DB."""
    if not settings.GOOGLE_API_KEY:
        pytest.skip("GOOGLE_API_KEY not set")
        
    # Setup DB
    await init_db()
    
    # Create Canvas
    canvas = await canvas_service.get_or_create_canvas_for_chat("integration_test_chat")
    
    # Real Image
    # Assuming the file is now in tests/assets/test_image.jpg
    real_image_path = Path("tests/assets/test_image.jpg")
    if not real_image_path.exists():
        pytest.fail(f"Test image not found at {real_image_path}")
        
    file_data = real_image_path.read_bytes()
    
    element = await image_service.process_image(
        file_data=file_data,
        original_filename="integration_test.jpg",
        created_by="tester",
        canvas_id=canvas.id
    )
    
    # Verify Element
    assert element is not None
    assert element.type == "image"
    assert element.content is not None
    assert "file_path" in element.attributes
    
    # Verify File Exists
    file_path = Path(element.attributes["file_path"])
    # Note: file_path is relative, we need to resolve it relative to project root or storage dir
    # In ImageService we store relative to project root (implied)
    full_path = Path(".").resolve() / file_path
    assert full_path.exists()
    
    # Verify DB Persistence
    fetched_element = await canvas_service.get_element(element.id)
    assert fetched_element is not None
    assert fetched_element.id == element.id
    
    # Cleanup (Optional, but good for heavy tests)
    # os.remove(full_path)
