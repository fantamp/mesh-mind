from typing import List, Optional
from datetime import datetime
import uuid
from sqlmodel import select, col
from sqlalchemy.orm import selectinload

from ai_core.storage.db import async_session
from ai_core.common.models import Canvas, CanvasElement, CanvasFrame

class CanvasService:
    
    async def get_or_create_canvas_for_chat(self, chat_id: str, create_if_not_found: bool = True) -> Canvas:
        """
        Retrieves a canvas accessible by the given chat_id, or creates one if none exists.
        For MVP, we assume 1:1 mapping, but the schema supports N:N.
        """
        auth_key = f"telegram:chat:{chat_id}"
        
        async with async_session() as session:
            # 1. Try to find a canvas where access_rules contains this chat_id
            # Note: JSON containment query depends on DB. For SQLite, we might need a simpler approach or custom function.
            # For MVP/SQLite, we'll fetch all and filter in python if needed, or use a simpler convention.
            # Let's try a direct query assuming we can filter.
            # Actually, for MVP, let's just query by a convention or name if we want to be safe with SQLite JSON.
            # BUT, let's try to do it right.
            
            # Optimization: For MVP, let's just select all canvases and filter in python. 
            # It's not efficient for production but safe for SQLite without extensions.
            statement = select(Canvas)
            result = await session.execute(statement)
            canvases = result.scalars().all()
            
            for canvas in canvases:
                if auth_key in canvas.access_rules:
                    return canvas
            
            # 2. If not found, create new
            if not create_if_not_found:
                raise ValueError(f"Canvas not found for chat_id: {chat_id}")

            new_canvas = Canvas(
                name=f"Canvas for chat_id={chat_id}",
                access_rules=[auth_key]
            )
            session.add(new_canvas)
            await session.commit()
            await session.refresh(new_canvas)
            return new_canvas

    async def add_element(
        self,
        canvas_id: uuid.UUID,
        type: str,
        content: str,
        created_by: str,
        attributes: dict = None,
        frame_id: Optional[uuid.UUID] = None,
        element_id: Optional[uuid.UUID] = None
    ) -> CanvasElement:
        """
        Adds a new element to the canvas.
        """
        if attributes is None:
            attributes = {}
            
        # Store created_by in attributes
        attributes['created_by'] = created_by
            
        element = CanvasElement(
            id=element_id if element_id else uuid.uuid4(),
            canvas_id=canvas_id,
            # frame_id=frame_id, # REMOVED
            type=type,
            content=content,
            created_by=created_by,
            attributes=attributes
        )
        
        async with async_session() as session:
            session.add(element)
            await session.commit()
            await session.refresh(element)
            
            # If frame_id provided, link it
            if frame_id:
                await self.add_element_to_frame(element.id, frame_id)
                # Refresh to get updated state if needed, though link is separate
                
            return element

    async def get_element(self, element_id: uuid.UUID) -> Optional[CanvasElement]:
        """Retrieves a single element by ID."""
        async with async_session() as session:
            # Eagerly load frames to avoid DetachedInstanceError
            statement = select(CanvasElement).where(CanvasElement.id == element_id).options(selectinload(CanvasElement.frames))
            result = await session.execute(statement)
            return result.scalars().first()

    async def get_elements(
        self,
        canvas_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        type: Optional[str] = None,
        since: Optional[datetime] = None,
        frame_id: Optional[uuid.UUID] = None
    ) -> List[CanvasElement]:
        """
        Retrieves elements from a canvas with optional filtering.
        """
        async with async_session() as session:
            statement = select(CanvasElement).where(CanvasElement.canvas_id == canvas_id)
            
            if type:
                statement = statement.where(CanvasElement.type == type)
            
            if since:
                statement = statement.where(CanvasElement.created_at >= since)
                
            if frame_id:
                # Join with link table
                from ai_core.common.models import CanvasElementFrameLink
                statement = statement.join(CanvasElementFrameLink).where(CanvasElementFrameLink.frame_id == frame_id)
            
            statement = statement.order_by(CanvasElement.created_at.desc())
            statement = statement.offset(offset).limit(limit)
            
            # Eagerly load frames to avoid DetachedInstanceError when accessing el.frames later
            statement = statement.options(selectinload(CanvasElement.frames))
            
            result = await session.execute(statement)
            return result.scalars().all()

    async def create_frame(
        self,
        canvas_id: uuid.UUID,
        name: str,
        parent_id: Optional[uuid.UUID] = None,
        meta: dict = None
    ) -> CanvasFrame:
        """Creates a new frame."""
        if meta is None:
            meta = {}
            
        frame = CanvasFrame(
            canvas_id=canvas_id,
            name=name,
            parent_id=parent_id,
            meta=meta
        )
        async with async_session() as session:
            session.add(frame)
            await session.commit()
            await session.refresh(frame)
            return frame

    async def delete_frame(self, frame_id: uuid.UUID) -> bool:
        """Deletes a frame. Links to elements are removed (cascade), elements stay."""
        async with async_session() as session:
            frame = await session.get(CanvasFrame, frame_id)
            if not frame:
                return False
            
            # Links should be deleted by cascade if configured, or we delete manually.
            # Let's delete links manually to be safe.
            stmt = delete(CanvasElementFrameLink).where(CanvasElementFrameLink.frame_id == frame_id)
            await session.execute(stmt)
            
            await session.delete(frame)
            await session.commit()
            return True

    async def update_canvas(self, canvas_id: uuid.UUID, name: str) -> Optional[Canvas]:
        """Updates canvas name."""
        async with async_session() as session:
            canvas = await session.get(Canvas, canvas_id)
            if not canvas:
                return None
            canvas.name = name
            session.add(canvas)
            await session.commit()
            await session.refresh(canvas)
            return canvas



    async def get_frame(self, frame_id: uuid.UUID) -> Optional[CanvasFrame]:
        """Retrieves a single frame by ID."""
        async with async_session() as session:
            return await session.get(CanvasFrame, frame_id)

    async def get_frames(self, canvas_id: uuid.UUID) -> List[CanvasFrame]:
        """Returns all frames for a canvas."""
        async with async_session() as session:
            statement = select(CanvasFrame).where(CanvasFrame.canvas_id == canvas_id)
            result = await session.execute(statement)
            return result.scalars().all()

    async def update_frame(self, frame_id: uuid.UUID, name: str) -> Optional[CanvasFrame]:
        """Updates frame name."""
        async with async_session() as session:
            frame = await session.get(CanvasFrame, frame_id)
            if not frame:
                return None
            frame.name = name
            session.add(frame)
            await session.commit()
            await session.refresh(frame)
            return frame

    async def update_element(
        self, 
        element_id: uuid.UUID, 
        name: Optional[str] = None,
        content: Optional[str] = None,
        type: Optional[str] = None,
        attributes: Optional[dict] = None,
        attributes_to_remove: Optional[List[str]] = None
    ) -> Optional[CanvasElement]:
        """Updates element properties."""
        async with async_session() as session:
            element = await session.get(CanvasElement, element_id)
            if not element:
                return None
            
            if name is not None:
                element.name = name
            
            if content is not None:
                element.content = content
                
            if type is not None:
                element.type = type
                
            if attributes or attributes_to_remove:
                # Create a copy of existing attributes to modify
                # Note: SQLModel/SQLAlchemy JSON mutation tracking can be tricky, 
                # so it's safer to replace the dict or flag modified.
                new_attrs = dict(element.attributes) if element.attributes else {}
                
                if attributes:
                    new_attrs.update(attributes)
                    
                if attributes_to_remove:
                    for key in attributes_to_remove:
                        new_attrs.pop(key, None)
                        
                element.attributes = new_attrs
                
            session.add(element)
            await session.commit()
            await session.refresh(element)
            return element

    async def add_element_to_frame(self, element_id: uuid.UUID, frame_id: uuid.UUID) -> bool:
        """Adds an element to a frame (creates link)."""
        from ai_core.common.models import CanvasElementFrameLink
        async with async_session() as session:
            # Check if link exists
            link = await session.get(CanvasElementFrameLink, (frame_id, element_id))
            if link:
                return True # Already there
            
            link = CanvasElementFrameLink(frame_id=frame_id, element_id=element_id)
            session.add(link)
            try:
                await session.commit()
                return True
            except Exception:
                return False

    async def remove_element_from_frame(self, element_id: uuid.UUID, frame_id: uuid.UUID) -> bool:
        """Removes an element from a frame (deletes link)."""
        from ai_core.common.models import CanvasElementFrameLink
        async with async_session() as session:
            link = await session.get(CanvasElementFrameLink, (frame_id, element_id))
            if link:
                await session.delete(link)
                await session.commit()
                return True
            return False

# Singleton instance
canvas_service = CanvasService()
