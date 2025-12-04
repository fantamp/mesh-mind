import os
import shutil
import uuid
import tempfile
import re
from pathlib import Path
from typing import Optional, Tuple
import google.generativeai as genai
from loguru import logger

from ai_core.common.config import settings
from ai_core.services.canvas_service import canvas_service
from ai_core.common.models import CanvasElement
from ai_core.common.prompts import IMAGE_DESCRIPTION_PROMPT

class ImageService:
    def __init__(self):
        self.storage_dir = Path(settings.IMAGES_PATH)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_FAST)
        else:
            logger.error("GOOGLE_API_KEY not set. Image description will fail.")
            raise ValueError("GOOGLE_API_KEY is required for ImageService")

    async def save_temp_image(self, file_data: bytes, filename: str) -> Path:
        """Saves image to system temporary directory."""
        # Create a temp file that persists until we move it
        fd, temp_path = tempfile.mkstemp(suffix=Path(filename).suffix, prefix="mesh_mind_img_")
        with os.fdopen(fd, 'wb') as f:
            f.write(file_data)
        return Path(temp_path)

    async def generate_description(self, file_path: Path) -> str:
        """Generates description using Gemini Vision."""
        if not self.model:
            raise ValueError("Gemini API not configured")
        
        try:
            # Read file data
            file_data = file_path.read_bytes()
            mime_type = "image/jpeg"
            if file_path.suffix.lower() == ".png":
                mime_type = "image/png"
            elif file_path.suffix.lower() == ".webp":
                mime_type = "image/webp"
            
            image_part = {
                "mime_type": mime_type,
                "data": file_data
            }
            
            # Use run_in_executor if generate_content is blocking (it is synchronous in google-generativeai)
            # But for now let's call it directly, assuming it's fast enough or we accept blocking.
            # Ideally we should wrap it.
            result = self.model.generate_content([IMAGE_DESCRIPTION_PROMPT, image_part])
            return result.text
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            raise

    def _extract_slug(self, description: str) -> str:
        """Extracts slug from the description."""
        try:
            # Look for "5) Slug: ..." or just "Slug: ..." or line starting with "5)"
            # Regex to find the slug line
            # Handle cases: "5) Slug: value", "Slug: value", "5) value"
            match = re.search(r"(?:5\)|Slug:)\s*(?:Slug:?\s*)?([a-zA-Z0-9_]+)", description, re.IGNORECASE)
            if match:
                slug = match.group(1).lower()
                # If we accidentally captured "slug" itself (e.g. "5) Slug"), try next word?
                # But the regex (?:Slug:?\s*)? should consume "Slug:" if present.
                if slug == "slug":
                     # Try to find next word
                     remaining = description[match.end():]
                     match2 = re.search(r"\s*([a-zA-Z0-9_]+)", remaining)
                     if match2:
                         return match2.group(1).lower()
                return slug
            
            # Fallback: try to find the last line if it looks like a slug
            lines = description.strip().split('\n')
            last_line = lines[-1].strip()
            if re.match(r"^[a-zA-Z0-9_]+$", last_line):
                return last_line.lower()

            # Fallback to heuristic
            return self._generate_slug_heuristic(description)
        except Exception:
            return "image"

    def _generate_slug_heuristic(self, description: str) -> str:
        """Generates a short slug from the description (fallback)."""
        try:
            lines = description.strip().split('\n')
            first_line = lines[0]
            # Remove non-alphanumeric (except spaces)
            clean_line = "".join(c for c in first_line if c.isalnum() or c.isspace())
            words = clean_line.split()[:2]
            # Transliteration is hard without lib, so just use what we have or default
            slug = "_".join(words).lower()
            if not slug or not re.match(r"^[a-zA-Z0-9_]+$", slug):
                return "image"
            return slug
        except Exception:
            return "image"

    def _get_sharded_path(self, element_id: uuid.UUID) -> Path:
        """Generates sharded path: data/images/ab/cd/"""
        id_str = str(element_id).replace("-", "")
        shard1 = id_str[:2]
        shard2 = id_str[2:4]
        path = self.storage_dir / shard1 / shard2
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def process_image(
        self, 
        file_data: bytes, 
        original_filename: str, 
        created_by: str, 
        canvas_id: uuid.UUID
    ) -> CanvasElement:
        """
        Orchestrates the full image processing pipeline.
        """
        temp_path = await self.save_temp_image(file_data, original_filename)
        
        try:
            # 1. Get Description
            description = await self.generate_description(temp_path)
            
            # 2. Generate ID and Paths
            element_id = uuid.uuid4()
            slug = self._extract_slug(description)
            ext = Path(original_filename).suffix
            if not ext:
                ext = ".jpg" # Default
                
            sharded_dir = self._get_sharded_path(element_id)
            final_filename = f"{element_id}_{slug}{ext}"
            final_path = sharded_dir / final_filename
            
            # 3. Move file
            shutil.move(temp_path, final_path)
            
            # 4. Create Element
            # Relative path for storage
            relative_path = final_path.relative_to(Path(".").resolve() if Path(".").resolve() in final_path.parents else ".")
            
            attributes = {
                "file_path": str(relative_path),
                "original_filename": original_filename,
                "mime_type": "image/" + ext.replace(".", "") # Rough guess
            }
            
            element = await canvas_service.add_element(
                canvas_id=canvas_id,
                type="image",
                content=description,
                created_by=created_by,
                attributes=attributes,
                element_id=element_id
            )
            
            return element
            
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            if temp_path.exists():
                os.remove(temp_path)
            raise

image_service = ImageService()
