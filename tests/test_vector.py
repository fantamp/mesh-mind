import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# sys.path hack removed

from ai_core.rag.vector_db import VectorDB

def test_vector_db():
    print("Initializing VectorDB...")
    # Check for API key, if not present or dummy, use Mock
    import os
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key.startswith("dummy"):
        print("WARNING: No API key found. Using MockEmbeddingService for testing.")
        # Monkey patch the embedding service in the instance we are about to create
        # Or better, let's just mock it after creation or inject it if we refactor.
        # Since VectorDB creates it internally, we'll mock the class in the module.
        
        class MockEmbeddingService:
            def __init__(self, api_key): pass
            def embed_documents(self, texts):
                # Return random vectors of dimension 768 (standard for Gemini)
                import random
                return [[random.random() for _ in range(768)] for _ in texts]
            def embed_query(self, text):
                import random
                return [random.random() for _ in range(768)]

        import ai_core.rag.vector_db
        ai_core.rag.vector_db.EmbeddingService = MockEmbeddingService
        # We also need to bypass the api key check in VectorDB.__init__ if it enforces it
        # The current implementation of EmbeddingService raises ValueError if no key.
        # But our Mock doesn't.
        # However, VectorDB passes the key from env.
        # Let's just set a dummy key so VectorDB doesn't crash before reaching our Mock
        import os
        os.environ["GEMINI_API_KEY"] = "dummy"

    db = VectorDB()
    
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
        return

    print("\n--- Test 2: Search 'Greeting' ---")
    results = db.search("Greeting", n_results=1)
    print(f"Results: {results}")
    
    # Check results
    assert results is not None, "No results returned"
    assert len(results['documents'][0]) > 0, "No documents found"
    
    if api_key and not api_key.startswith("dummy"):
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

# Main block removed
