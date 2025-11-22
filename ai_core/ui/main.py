import streamlit as st
import sys
from pathlib import Path
import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_core.rag.vector_db import VectorDB
from ai_core.common.config import settings

st.set_page_config(
    page_title="Mesh Mind Admin",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Mesh Mind Admin Dashboard")

def get_stats():
    try:
        vector_db = VectorDB()
        # ChromaDB collection count
        doc_count = vector_db.collection.count()
        
        # For now we don't have a message store, so we mock it or check if we can get it from somewhere.
        # In MVP we might not have persistent message store yet besides logs or memory.
        # Let's just show doc count for now.
        
        return {
            "total_documents": doc_count,
            "last_ingestion": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Mock for now as we don't track ingestion time globally
        }
    except Exception as e:
        st.error(f"Error connecting to VectorDB: {e}")
        return {"total_documents": 0, "last_ingestion": "N/A"}

stats = get_stats()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Documents (Chunks)", value=stats["total_documents"])

with col2:
    st.metric(label="Last Ingestion", value=stats["last_ingestion"])

with col3:
    st.metric(label="System Status", value="Online")

st.markdown("---")
st.subheader("Welcome to Mesh Mind Admin")
st.markdown("""
Use the sidebar to navigate:
- **Knowledge Base**: Manage documents and ingestion.
- **Chat / Playground**: Test agents manually.
""")
