import streamlit as st
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_core.services.agent_service import run_qa as ask_question
from ai_core.services.agent_service import run_document_summarizer as summarize_documents
from ai_core.common.config import settings
from ai_core.common.models import DomainMessage
from ai_core.rag.vector_db import VectorDB
import datetime

st.set_page_config(page_title="Chat Playground", page_icon="💬", layout="wide")

st.title("💬 Chat Playground")

# Initialize VectorDB to fetch chat_ids
@st.cache_resource
def get_vector_db():
    return VectorDB()

vector_db = get_vector_db()

# --- Sidebar ---
st.sidebar.header("Context Selection")
available_chat_ids = vector_db.get_unique_chat_ids()

# Add option to enter a new/custom chat_id
chat_id_selection = st.sidebar.selectbox(
    "Select Chat ID", 
    options=["web-ui"] + available_chat_ids, # Default "web-ui" always available
    index=0
)

# Allow custom input if needed (optional, but good for testing)
custom_chat_id = st.sidebar.text_input("Or enter custom Chat ID", placeholder="e.g. new-context")
selected_chat_id = custom_chat_id.strip() if custom_chat_id else chat_id_selection

st.sidebar.markdown(f"**Current Context:** `{selected_chat_id}`")

if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = selected_chat_id

# Clear history if chat_id changes (optional, but keeps context clean)
if st.session_state.current_chat_id != selected_chat_id:
    st.session_state.messages = []
    st.session_state.current_chat_id = selected_chat_id

# --- Chat Interface ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            with st.expander("Sources"):
                for source in msg["sources"]:
                    st.markdown(f"**Source**: {source.get('metadata', {}).get('source', 'Unknown')}")
                    st.text(source.get('content', ''))

# Input
if prompt := st.chat_input(f"Message in {selected_chat_id}..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = ""
            
            try:
                # Check for commands
                if prompt.strip().startswith("/summary"):
                    # Summarize logic
                    response_text = summarize_documents(chat_id=selected_chat_id)
                else:
                    # QA Logic
                    response_text = ask_question(prompt, user_id="admin_ui_user", chat_id=selected_chat_id)
            
            except Exception as e:
                response_text = f"Error: {e}"

            st.markdown(response_text)
            
            # Save assistant message
            msg_data = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(msg_data)
