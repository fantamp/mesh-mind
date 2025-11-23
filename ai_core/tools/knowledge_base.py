from typing import List, Optional
from ai_core.rag.vector_db import VectorDB
from ai_core.common.logging import logger

# Initialize Vector Store once
_vector_store = VectorDB()

def search_knowledge_base(query: str, chat_id: str) -> str:
    """
    Searches the knowledge base (Vector DB) for relevant information.
    Use this tool when the user asks a question requiring factual information from documents.

    Args:
        query: The search query.
        chat_id: The chat ID to filter the search.

    Returns:
        A string containing found text fragments with sources.
    """
    logger.info(f"Searching knowledge base: {query} (chat_id={chat_id})")
    
    try:
        results = _vector_store.search(query, n_results=5, chat_id=chat_id)
        
        if not results or not results.get('documents') or not results['documents'][0]:
            return "No relevant information found in the knowledge base."
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        formatted_results = []
        for idx, (text, metadata) in enumerate(zip(documents, metadatas), 1):
            source = metadata.get("source", "unknown")
            formatted_results.append(f"[{idx}] (source: {source})\n{text}")
        
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return f"Search error: {str(e)}"

def fetch_documents(chat_id: str, tags: Optional[str] = None, limit: int = 20) -> str:
    """
    Fetches documents from the knowledge base for a specific chat, optionally filtered by tags.
    Useful for summarizing accumulated knowledge.

    Args:
        chat_id: The chat ID to filter documents.
        tags: Optional comma-separated tags to filter by (e.g. "legal,contract").
        limit: Maximum number of documents to retrieve.

    Returns:
        A string containing the combined text of the documents.
    """
    logger.info(f"Fetching documents for chat_id={chat_id}, tags={tags}")
    
    where = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if len(tag_list) == 1:
            where = {"tags": {"$contains": tag_list[0]}}
        elif len(tag_list) > 1:
             where = {"$or": [{"tags": {"$contains": tag}} for tag in tag_list]}

    try:
        documents = _vector_store.get_documents(limit=limit, where=where, chat_id=chat_id)
        
        if not documents:
            return "No documents found."
            
        return "\n\n---\n\n".join(documents)

    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        return f"Error fetching documents: {str(e)}"
