import streamlit as st
import sys
import tempfile
import os
from pathlib import Path
import pandas as pd
import datetime

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

# Chat ID input for context isolation (Always visible)
chat_id_input = st.text_input("Assign to Chat ID (optional)", value="web-ui", help="Specify which chat context this file belongs to.")

uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "md", "eml", "mp3", "wav", "ogg", "m4a"])
tags_input = st.text_input("Tags (comma separated)", placeholder="e.g. Law, Manual, V1")

if uploaded_file is not None:
    
    if st.button("Process & Ingest"):
        with st.spinner("Processing..."):
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
                
                # Add chat_id and date to base metadata
                effective_chat_id = chat_id_input.strip() if chat_id_input else "web-ui"
                result.metadata["chat_id"] = effective_chat_id
                result.metadata["date"] = datetime.datetime.now().isoformat()
                
                # Chunk
                chunks = recursive_character_split(result.text)
                
                # Prepare metadata for each chunk
                metadatas = []
                for i in range(len(chunks)):
                    chunk_metadata = result.metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    chunk_metadata["original_filename"] = uploaded_file.name
                    metadatas.append(chunk_metadata)
                
                # Add to VectorDB
                vector_db.add_texts(texts=chunks, metadatas=metadatas, chat_id=effective_chat_id)
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

st.markdown("---")

# --- File Management Section ---
st.subheader("Manage Files")

# Fetch all metadata to find unique files
# Note: This might be slow for large DBs, but fine for MVP
try:
    all_data = vector_db.collection.get(include=["metadatas"])
    if all_data and all_data['metadatas']:
        files_data = {}
        for meta in all_data['metadatas']:
            filename = meta.get("original_filename", "Unknown")
            if filename not in files_data:
                files_data[filename] = {
                    "count": 0,
                    "date": meta.get("date", "Unknown"),
                    "tags": meta.get("tags", [])
                }
            files_data[filename]["count"] += 1
            
        # Convert to DataFrame
        files_list = []
        for fname, info in files_data.items():
            files_list.append({
                "Filename": fname,
                "Date": info["date"],
                "Chunks": info["count"],
                "Tags": str(info["tags"])
            })
            
        if files_list:
            df_files = pd.DataFrame(files_list)
            st.dataframe(df_files, use_container_width=True)
            
            # Delete functionality
            st.write("### Delete File")
            file_to_delete = st.selectbox("Select file to delete", [f["Filename"] for f in files_list])
            
            if st.button("Delete Selected File"):
                if file_to_delete:
                    with st.spinner(f"Deleting {file_to_delete}..."):
                        vector_db.delete(where={"original_filename": file_to_delete})
                        st.success(f"Deleted {file_to_delete}")
                        st.rerun()
        else:
            st.info("No files found in the database.")
    else:
        st.info("Database is empty.")
except Exception as e:
    st.error(f"Error fetching files: {e}")
