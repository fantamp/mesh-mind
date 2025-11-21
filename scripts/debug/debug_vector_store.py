import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from ai_core.common.config import settings

# Connect to ChromaDB
client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
collection = client.get_collection(name="mesh_mind_v1")

# Get all documents
all_docs = collection.get()

print(f"Total documents in vector store: {len(all_docs['ids'])}\n")

# Group by source/type
from collections import defaultdict
by_type = defaultdict(list)

for i, doc_id in enumerate(all_docs['ids']):
    metadata = all_docs['metadatas'][i]
    doc_text = all_docs['documents'][i]
    source = metadata.get('source', 'unknown')
    doc_type = metadata.get('type', 'unknown')
    chat_id = metadata.get('chat_id', 'N/A')
    
    key = f"{source}/{doc_type}"
    by_type[key].append({
        'id': doc_id,
        'chat_id': chat_id,
        'text': doc_text[:100],  # First 100 chars
        'metadata': metadata
    })

print("=== Documents by Type ===\n")
for key, docs in sorted(by_type.items()):
    print(f"\n{key} ({len(docs)} documents):")
    for doc in docs[-5:]:  # Last 5 of each type
        print(f"  - ID: {doc['id'][:8]}...")
        print(f"    Chat ID: {doc['chat_id']}")
        print(f"    Text: {doc['text']}")
        print(f"    Metadata: {doc['metadata']}")
        print()

# Search for Austria messages
print("\n=== Searching for 'Австрали' ===\n")
import google.generativeai as genai
from ai_core.rag.vector_db import EmbeddingService

embedding_service = EmbeddingService(api_key=settings.GOOGLE_API_KEY)
query_embedding = embedding_service.embed_query("столица Австралии")

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10
)

if results['documents']:
    for i, doc in enumerate(results['documents'][0]):
        print(f"{i+1}. {doc}")
        print(f"   Metadata: {results['metadatas'][0][i]}")
        print()
else:
    print("No results found!")
