import streamlit as st
import sys
import tempfile
import os
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_core.rag.vector_db import VectorDB
from ai_core.ingest.parsers import DocumentParser
from ai_core.ingest.chunking import recursive_character_split

st.set_page_config(page_title="Knowledge Base", page_icon="📚", layout="wide")

st.title("📚 Knowledge Base")

@st.cache_resource
def get_vector_db():
    return VectorDB()

vector_db = get_vector_db()

# --- Upload Section ---
st.subheader("Upload Documents")
uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "md", "eml"])
tags_input = st.text_input("Tags (comma separated)", placeholder="e.g. Law, Manual, V1")

if uploaded_file is not None:
    if st.button("Ingest File"):
        with st.spinner("Ingesting..."):
            try:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = Path(tmp_file.name)
                
                # Parse
                result = DocumentParser.parse(tmp_path)
                
                # Add tags
                if tags_input:
                    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                    result.metadata["tags"] = tags
                
                # Chunk
                chunks = recursive_character_split(result.text)
                
                # Prepare metadata
                metadatas = []
                for i in range(len(chunks)):
                    chunk_metadata = result.metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    chunk_metadata["original_filename"] = uploaded_file.name
                    metadatas.append(chunk_metadata)
                
                # Add to VectorDB
                vector_db.add_texts(chunks, metadatas)
                
                st.success(f"Successfully ingested {len(chunks)} chunks from {uploaded_file.name}!")
                
                # Cleanup
                os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"Error during ingestion: {e}")

st.markdown("---")

# --- Search / View Section ---
st.subheader("Search / Inspect Chunks")
search_query = st.text_input("Search Knowledge Base", placeholder="Enter query...")

if search_query:
    results = vector_db.search(search_query, n_results=10)
    
    if results and results['documents']:
        data = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            data.append({
                "Score": results['distances'][0][i] if 'distances' in results else "N/A",
                "Content": doc,
                "Metadata": meta
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No results found.")
else:
    st.info("Enter a query to search the Knowledge Base.")

# Note: Listing all documents in ChromaDB is not efficient/supported directly via simple API call 
# without fetching all. For MVP, search is the primary way to inspect.
