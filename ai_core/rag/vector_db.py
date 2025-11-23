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

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None, chat_id: str = None):
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

        # Ensure metadata has date and chat_id
        import datetime
        current_date = datetime.datetime.now().isoformat()
        for meta in metadatas:
            if "date" not in meta:
                meta["date"] = current_date
            if chat_id:
                meta["chat_id"] = chat_id

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} documents to vector store (chat_id={chat_id}).")

    def search(self, query: str, n_results: int = 5, filters: Dict[str, Any] = None, chat_id: str = None) -> Dict[str, Any]:
        """
        Search for similar documents.
        """
        query_embedding = self.embedding_service.embed_query(query)

        # Construct where clause
        where_clause = filters if filters else {}
        
        if chat_id:
            # If we already have filters, we need to combine them using $and
            if where_clause:
                # If it's already an $and clause, append to it
                if "$and" in where_clause:
                    where_clause["$and"].append({"chat_id": chat_id})
                else:
                    # Wrap existing filter and chat_id in $and
                    where_clause = {
                        "$and": [
                            where_clause,
                            {"chat_id": chat_id}
                        ]
                    }
            else:
                where_clause = {"chat_id": chat_id}

        # ChromaDB expects None if no filter, not empty dict
        final_where = where_clause if where_clause else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=final_where # ChromaDB filter syntax
        )
        return results

    def get_documents(self, limit: int = 100, where: Dict[str, Any] = None, chat_id: str = None) -> List[str]:
        """
        Get documents from the vector store based on metadata filters.
        """
        # Construct where clause
        where_clause = where if where else {}
        
        if chat_id:
            if where_clause:
                if "$and" in where_clause:
                    where_clause["$and"].append({"chat_id": chat_id})
                else:
                    where_clause = {
                        "$and": [
                            where_clause,
                            {"chat_id": chat_id}
                        ]
                    }
            else:
                where_clause = {"chat_id": chat_id}

        final_where = where_clause if where_clause else None

        results = self.collection.get(
            limit=limit,
            where=final_where
        )
        
        return results['documents'] if results and 'documents' in results else []

    def delete(self, where: Dict[str, Any] = None):
        """
        Delete documents from the vector store based on metadata filters.
        """
        if not where:
            logger.warning("Delete called without filters. Ignoring to prevent deleting everything.")
            return

        self.collection.delete(where=where)
        logger.info(f"Deleted documents matching {where}")

    def get_unique_chat_ids(self) -> List[str]:
        """
        Retrieves all unique chat_ids present in the metadata.
        """
        try:
            # Fetch all metadata
            # Note: This might be slow for very large datasets, but acceptable for MVP
            results = self.collection.get(include=["metadatas"])
            if not results or not results.get("metadatas"):
                return []
            
            chat_ids = set()
            for meta in results["metadatas"]:
                if meta and "chat_id" in meta and meta["chat_id"]:
                    chat_ids.add(str(meta["chat_id"]))
            
            return sorted(list(chat_ids))
        except Exception as e:
            logger.error(f"Error fetching unique chat_ids: {e}")
            return []

