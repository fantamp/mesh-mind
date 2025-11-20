import os
import uuid
from datetime import datetime
from typing import Literal

from ai_core.common.config import settings

def _get_storage_path(file_type: str) -> str:
    """
    Determines the storage path based on file type.
    Voice files go to data/media/voice/{YYYY}/{MM}/{DD}/
    Docs go to data/docs/
    """
    base_path = settings.MEDIA_PATH # defaults to data/media
    
    if file_type == "voice":
        now = datetime.utcnow()
        return os.path.join(base_path, "voice", now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    elif file_type == "doc":
        # Assuming docs go to a sibling directory or specific docs directory
        # The spec says data/docs/
        # settings.MEDIA_PATH is data/media.
        # Let's assume data/docs is at the same level as data/media if we follow the spec strictly.
        # Or we can put it under data/media/docs.
        # Spec: "data/docs/"
        # Config: DB_PATH="data/db/...", MEDIA_PATH="data/media"
        # Let's use a relative path from the project root for docs to match spec "data/docs/"
        return "data/docs"
    else:
        return os.path.join(base_path, "misc")

def save_file(file_content: bytes, filename: str, file_type: Literal["voice", "doc", "misc"] = "misc") -> str:
    """
    Saves a file to the file system and returns the absolute path.
    Appends a UUID to the filename to ensure uniqueness.
    """
    target_dir = _get_storage_path(file_type)
    os.makedirs(target_dir, exist_ok=True)
    
    # Generate unique filename
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(target_dir, unique_filename)
    
    # Write file
    with open(file_path, "wb") as f:
        f.write(file_content)
        
    return os.path.abspath(file_path)
