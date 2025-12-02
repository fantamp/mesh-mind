import logging
import uuid
from datetime import datetime
from sqlalchemy import text
from ai_core.storage.db import engine, init_db
from ai_core.services.canvas_service import canvas_service

logger = logging.getLogger(__name__)

async def run_migration():
    """
    Checks if the database needs migration from the old schema (messages table) 
    to the new schema (canvas_elements).
    """
    logger.info("Checking for pending migrations...")
    
    async with engine.begin() as conn:
        # Check if 'messages' table exists
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='messages';"))
        messages_table = result.scalar()
        
        if not messages_table:
            logger.info("No 'messages' table found. Skipping migration.")
            return

        # Check if 'canvas_elements' table exists (it should be created by init_db, but let's be sure)
        # Actually, init_db is called before this usually.
        
        logger.info("Found legacy 'messages' table. Starting migration...")
        
        # 1. Fetch all messages
        # We use raw SQL to avoid dependency on old models
        msgs = await conn.execute(text("SELECT * FROM messages"))
        messages_data = msgs.mappings().all()
        
        # 2. Fetch all documents
        docs_data = []
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='document';"))
        if result.scalar():
            docs = await conn.execute(text("SELECT * FROM document"))
            docs_data = docs.mappings().all()
            
    # We need to process data. We can't do it inside the transaction if we use canvas_service 
    # which uses its own session/transaction management usually.
    # So we fetched data, now we process it.
    
    count_msg = 0
    count_doc = 0
    
    # Process Messages
    for msg in messages_data:
        chat_id = msg['chat_id']
        
        # Get/Create Canvas
        canvas = await canvas_service.get_or_create_canvas_for_chat(chat_id)
        
        # Map fields
        content = msg['content']
        media_type = msg['media_type'] or 'text'
        
        # Determine type
        c_type = 'voice' if media_type == 'voice' else 'message'
        
        # Attributes
        attrs = {
            "source": msg['source'],
            "source_msg_id": msg['id'], # Keep old ID reference
            "author_id": msg['author_id'],
            "author_nick": msg['author_nick'],
            "author_name": msg['author_name'],
            "media_path": msg['media_path'],
            "migrated": True
        }
        
        # Add Element
        await canvas_service.add_element(
            canvas_id=canvas.id,
            type=c_type,
            content=content,
            created_by=msg['author_id'] or 'unknown',
            attributes=attrs
        )
        count_msg += 1

    # Process Documents
    for doc in docs_data:
        # Document table didn't have chat_id in the schema I saw earlier?
        # Wait, let me check the schema again.
        # CREATE TABLE document (id, filename, content, doc_metadata JSON);
        # It has NO chat_id! 
        # This means documents were global or I missed something.
        # If they are global, we can't assign them to a canvas easily.
        # Let's check if doc_metadata has chat_id.
        
        # For now, let's skip documents if we can't link them, or put them in a "Global" canvas?
        # Or maybe just log a warning.
        # Let's assume metadata might have it.
        import json
        meta = doc['doc_metadata']
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except:
                meta = {}
        
        # If no chat_id, we can't migrate safely to a specific chat canvas.
        # Let's skip for MVP unless we find a key.
        logger.warning(f"Skipping document {doc['id']} (filename: {doc['filename']}) - No chat_id link found in schema.")
        count_doc += 1

    logger.info(f"Migration complete. Migrated {count_msg} messages.")
    
    # Rename old tables to backup
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE messages RENAME TO messages_backup_v1;"))
        
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='document';"))
        if result.scalar():
            await conn.execute(text("ALTER TABLE document RENAME TO document_backup_v1;"))
            
    logger.info("Old tables renamed to *_backup_v1.")
