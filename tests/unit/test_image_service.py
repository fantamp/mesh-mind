import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import os
from pathlib import Path
from ai_core.services.image_service import ImageService

@pytest.fixture
def image_service():
    with patch("ai_core.services.image_service.genai") as mock_genai:
        service = ImageService()
        service.model = MagicMock()
        return service

@pytest.mark.asyncio
async def test_save_temp_image(image_service):
    file_data = b"fake_image_data"
    filename = "test.jpg"
    
    # We can let it use real tempfile, just check it exists
    path = await image_service.save_temp_image(file_data, filename)
    try:
        assert path.exists()
        assert path.read_bytes() == file_data
        assert path.suffix == ".jpg"
    finally:
        if path.exists():
            os.remove(path)

def test_slug_extraction(image_service):
    # Test extraction from LLM response
    description = """
    1) Краткое описание:
    Short desc.
    
    2) Подробное описание:
    Detailed desc.
    
    3) Текст на изображении (если есть):
    - Text.
    
    4) Ключевые сущности и теги:
    - Tags.
    
    5) Slug:
    my_cool_image
    """
    slug = image_service._extract_slug(description)
    assert slug == "my_cool_image"
    
    # Test fallback to heuristic
    description_fallback = "Just a cat on a sofa"
    slug = image_service._extract_slug(description_fallback)
    assert slug == "just_a" # heuristic takes first 2 words

def test_sharded_path(image_service):
    element_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    # 12345678... -> 12/34/
    path = image_service._get_sharded_path(element_id)
    assert "data/images/12/34" in str(path)

@pytest.mark.asyncio
async def test_process_image_flow(image_service):
    # Setup mocks
    image_service.save_temp_image = AsyncMock(return_value=Path("tmp/test.jpg"))
    image_service.generate_description = AsyncMock(return_value="A test image\n\n5) Slug:\ntest_slug")
    image_service._get_sharded_path = MagicMock(return_value=Path("data/images/test"))
    
    # Mock shutil.move
    with patch("shutil.move") as mock_move, \
         patch("ai_core.services.image_service.canvas_service.add_element", new_callable=AsyncMock) as mock_add_element:
        
        mock_add_element.return_value = MagicMock(id=uuid.uuid4())
        
        await image_service.process_image(
            file_data=b"data",
            original_filename="photo.jpg",
            created_by="user",
            canvas_id=uuid.uuid4()
        )
        
        # Verify calls
        image_service.save_temp_image.assert_called_once()
        image_service.generate_description.assert_called_once()
        mock_move.assert_called_once()
        mock_add_element.assert_called_once()
        
        # Verify element_id was passed
        call_kwargs = mock_add_element.call_args.kwargs
        assert "element_id" in call_kwargs
        assert call_kwargs["element_id"] is not None
