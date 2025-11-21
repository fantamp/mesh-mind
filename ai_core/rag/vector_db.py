import os
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from typing import List, Dict, Optional, Any
from loguru import logger

from ai_core.common.config import settings

class EmbeddingService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            # Gemini API supports batch embedding, but let's check limits.
            # For simplicity in this MVP, we might loop or use batch if supported easily.
            # genai.embed_content supports 'content' as a list.
            result = genai.embed_content(
                model=self.model,
                content=texts,
                task_type="retrieval_document",
                title="Embedding of list of strings"
            )
            # The result structure depends on input. If list, it returns 'embedding' as list of lists.
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

class VectorDB:
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            persist_directory = settings.CHROMA_PATH
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "mesh_mind_v1"
        
        # We need a custom embedding function wrapper for Chroma
        # Chroma expects an object with `__call__` that takes input: Documents -> Output: Embeddings
        self.embedding_service = EmbeddingService(api_key=settings.GOOGLE_API_KEY)
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # or l2
        )

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None):
        """
        Add texts to the vector store.
        If ids are not provided, they will be generated.
        """
        if not texts:
            return

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]

        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Generate embeddings explicitly using our service
        embeddings = self.embedding_service.embed_documents(texts)

        # Ensure metadata has date
        import datetime
        current_date = datetime.datetime.now().isoformat()
        for meta in metadatas:
            if "date" not in meta:
                meta["date"] = current_date

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} documents to vector store.")

    def search(self, query: str, n_results: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search for similar documents.
        """
        query_embedding = self.embedding_service.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters # ChromaDB filter syntax
        )
        return results
