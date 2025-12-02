from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Column
import uuid

# ============================================================================
# Canvas Models
# ============================================================================

class Canvas(SQLModel, table=True):
    """
    Root entity representing a space (e.g., a chat context).
    """
    __tablename__ = "canvases"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: Optional[str] = None
    
    # Access Rules: JSON list of strings, e.g. ["telegram:chat:-100123", "user:admin"]
    access_rules: List[str] = Field(default=[], sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    frames: List["CanvasFrame"] = Relationship(back_populates="canvas")
    elements: List["CanvasElement"] = Relationship(back_populates="canvas")


class CanvasElementFrameLink(SQLModel, table=True):
    __tablename__ = "canvas_element_frame_links"
    frame_id: uuid.UUID = Field(foreign_key="canvas_frames.id", primary_key=True)
    element_id: uuid.UUID = Field(foreign_key="canvas_elements.id", primary_key=True)

class CanvasFrame(SQLModel, table=True):
    """
    A grouping entity within a Canvas (like a folder or a visual frame).
    """
    __tablename__ = "canvas_frames"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    canvas_id: uuid.UUID = Field(foreign_key="canvases.id", index=True)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="canvas_frames.id")
    
    name: str
    meta: Dict[str, Any] = Field(default={}, sa_column=Column(JSON)) # UI coords, color, etc.
    
    # Relationships
    canvas: Canvas = Relationship(back_populates="frames")
    elements: List["CanvasElement"] = Relationship(back_populates="frames", link_model=CanvasElementFrameLink)
    

class CanvasElement(SQLModel, table=True):
    """
    Unified content entity: Message, Note, File, etc.
    """
    __tablename__ = "canvas_elements"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    canvas_id: uuid.UUID = Field(foreign_key="canvases.id", index=True)
    
    type: str = Field(index=True) # message, note, file, voice
    name: Optional[str] = None # Short human-readable name
    content: str
    
    created_by: str = Field(index=True) # e.g. telegram:user:123
    
    # Flexible attributes: source_msg_id, file_path, mime_type, etc.
    attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    canvas: Canvas = Relationship(back_populates="elements")
    frames: List[CanvasFrame] = Relationship(back_populates="elements", link_model=CanvasElementFrameLink)
