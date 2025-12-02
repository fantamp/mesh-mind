from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from ai_core.common.config import settings

# Import tools and sub-agents
from ai_core.tools.elements import fetch_elements

agent = LlmAgent(
    name="chat_summarizer",
    model=settings.GEMINI_MODEL_SMART,
    description="Agent responsible for summarizing chat history",
    instruction="""You are the Chat Summarizer.
Your goal is to summarize the chat history based on the user's request.

HOW TO WORK:
1.  **Fetch Elements**: Use the `fetch_elements` tool to retrieve chat history (messages, notes) from the database.
    *   You can specify `limit`, `since` time, or other criteria.
    *   If the user didn't specify a range, default to the last 50 elements or use your judgment.
2.  **Summarize**: Once you have the elements generate a summary in the same language as the user's request.
    
Do not try to summarize the text yourself as the tool is available.
""",
    tools=[
        fetch_elements, 
    ]
)
