from typing import AsyncGenerator, List, Dict, Any, Optional
from loguru import logger
from ai_core.storage.db import async_session
from ai_core.rag.vector_db import VectorDB

async def get_db_session() -> AsyncGenerator:
    async with async_session() as session:
        yield session

class MockVectorDB:
    def __init__(self):
        logger.warning("Using MockVectorDB because GEMINI_API_KEY is not set.")

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None):
        logger.info(f"[MOCK] Added {len(texts)} texts to vector store.")

    def search(self, query: str, n_results: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.info(f"[MOCK] Searching for: {query}")
        return {
            "ids": [["mock_id_1", "mock_id_2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [[
                {"source": "mock_source", "type": "text", "author": "mock_author"},
                {"source": "mock_source", "type": "doc", "author": "mock_author"}
            ]],
            "documents": [[
                "This is a mock result for your query.",
                "Another mock result from the vector store."
            ]]
        }

# Global instance to avoid re-initialization overhead if any
_vector_db = None

def get_vector_db() -> Any:
    global _vector_db
    if _vector_db is None:
        try:
            _vector_db = VectorDB()
        except ValueError as e:
            logger.error(f"Failed to initialize VectorDB: {e}")
            _vector_db = MockVectorDB()
        except Exception as e:
            logger.error(f"Unexpected error initializing VectorDB: {e}")
            _vector_db = MockVectorDB()
    return _vector_db
