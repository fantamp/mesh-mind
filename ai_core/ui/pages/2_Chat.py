import streamlit as st
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_core.agents.qa import ask_question
from ai_core.agents.summarizer import summarize
from ai_core.common.config import settings
from ai_core.common.models import Message
import datetime

st.set_page_config(page_title="Chat Playground", page_icon="💬", layout="wide")

st.title("💬 Chat Playground")

# --- Sidebar ---
agent_type = st.sidebar.radio("Select Agent", ["QA Agent", "Summarizer"])

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_agent" not in st.session_state:
    st.session_state.current_agent = agent_type

# Clear history if agent changes
if st.session_state.current_agent != agent_type:
    st.session_state.messages = []
    st.session_state.current_agent = agent_type

# --- Chat Interface ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            with st.expander("Sources"):
                for source in msg["sources"]:
                    st.markdown(f"**Source**: {source.get('metadata', {}).get('source', 'Unknown')}")
                    st.text(source.get('content', ''))

if prompt := st.chat_input("Ask something..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = ""
            sources = None
            
            try:
                if agent_type == "QA Agent":
                    # QA Agent returns a string with embedded sources
                    # We call the synchronous function directly
                    response_text = ask_question(prompt, user_id="admin_ui_user")
                    
                    # Attempt to extract sources if they are in a specific format, 
                    # but for now just display the text as is since ask_question returns formatted text
                    
                elif agent_type == "Summarizer":
                    # Summarizer expects a list of Message objects
                    # We create a dummy message from the prompt
                    msg = Message(
                        source="admin_ui",
                        author_id="admin",
                        author_name="Admin",
                        content=prompt,
                        timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    response_text = summarize([msg])
            
            except Exception as e:
                response_text = f"Error: {e}"

            st.markdown(response_text)
            # Sources are currently embedded in text for QA agent
            
            # Save assistant message
            msg_data = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(msg_data)
