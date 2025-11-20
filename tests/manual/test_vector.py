import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

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
    # Check if "Hello world" is in results
    if results and len(results['documents'][0]) > 0:
        if "Hello world" in results['documents'][0][0]:
            print("PASS: Found greeting.")
        elif api_key and not api_key.startswith("dummy"):
             print("FAIL: Did not find greeting (Real API used).")
        else:
             print("PASS: Search returned results (Mock mode, semantic match not guaranteed).")
    else:
        print("FAIL: No results returned.")

    print("\n--- Test 3: Search with Filter (type='doc') ---")
    results = db.search("programming", n_results=3, filters={"type": "doc"})
    print(f"Results: {results}")
    # Should verify that we don't get the chat message
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    
    is_filtered = True
    for m in metas:
        if m['type'] != 'doc':
            is_filtered = False
            break
    
    if is_filtered and len(docs) > 0:
        print("PASS: Filtering worked.")
    else:
        print("FAIL: Filtering failed.")

if __name__ == "__main__":
    test_vector_db()
