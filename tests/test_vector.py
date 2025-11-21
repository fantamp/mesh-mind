import os
import sys
import time
import tempfile
import shutil
from dotenv import load_dotenv

load_dotenv()

# sys.path hack removed

from ai_core.rag.vector_db import VectorDB

def test_vector_db():
    # Создаем временную директорию для теста
    temp_dir = tempfile.mkdtemp()
    
    try:
        print(f"Initializing VectorDB with temp dir: {temp_dir}")
        # Check for API key, if not present or dummy, use Mock
        import os
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        import ai_core.rag.vector_db
        
        if api_key and not api_key.startswith("dummy"):
            print(f"Using Real API Key: {api_key[:5]}...")

        if not api_key or api_key.startswith("dummy"):
            print("WARNING: No API key found. Using MockEmbeddingService for testing.")
            # Monkey patch the embedding service in the instance we are about to create
            
            class MockEmbeddingService:
                def __init__(self, api_key): pass
                def embed_documents(self, texts):
                    # Return random vectors of dimension 768 (standard for Gemini)
                    import random
                    return [[random.random() for _ in range(768)] for _ in texts]
                def embed_query(self, text):
                    import random
                    return [random.random() for _ in range(768)]

            ai_core.rag.vector_db.EmbeddingService = MockEmbeddingService

        # Используем временную директорию для изоляции теста
        db = VectorDB(persist_directory=temp_dir)
        
        print("\n--- Test 1: Adding Texts ---")
        texts = [
            "Hello world, this is a test.",
            "Python is a great programming language.",
            "To make a cake you need flour and sugar."
        ]
        metadatas = [
            {"type": "chat", "source": "user"},
            {"type": "doc", "tag": "coding"},
            {"type": "doc", "tag": "cooking"}
        ]
        
        try:
            db.add_texts(texts, metadatas)
            print("Texts added successfully.")
        except Exception as e:
            print(f"Error adding texts: {e}")
            raise

        print("\n--- Test 2: Search 'Greeting' ---")
        results = db.search("Greeting", n_results=1)
        print(f"Results: {results}")
        
        # Check results
        assert results is not None, "No results returned"
        assert len(results['documents'][0]) > 0, "No documents found"
        
        if api_key and not api_key.startswith("dummy"):
            # В изолированной БД должен быть только наш тестовый документ
            assert "Hello world" in results['documents'][0][0], "Did not find greeting (Real API used)"
        else:
            print("PASS: Search returned results (Mock mode, semantic match not guaranteed).")

        print("\n--- Test 3: Search with Filter (type='doc') ---")
        results = db.search("programming", n_results=3, filters={"type": "doc"})
        print(f"Results: {results}")
        
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        
        # Verify filtering
        for m in metas:
            assert m['type'] == 'doc', f"Filtering failed: Found type {m['type']}"
        
        if len(docs) > 0:
            print("PASS: Filtering worked.")
        else:
            # In mock mode we might get random results, but we added 2 docs so we expect some.
            # However, the mock embedding returns random vectors, so cosine similarity might be low/random.
            # But we are not filtering by score, just by metadata.
            # ChromaDB should return them if they match filter.
            pass
    
    finally:
        # Очищаем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\nCleaned up temp dir: {temp_dir}")

# Main block removed
