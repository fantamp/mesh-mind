"""
Summarizer Agent

Агент для генерации саммари истории чата используя Google ADK.
"""

from google.adk.agents import LlmAgent

from ai_core.common.config import settings
from ai_core.tools.messages import fetch_chat_messages
from ai_core.tools.knowledge_base import fetch_documents

# Создаём агента (один раз на уровне модуля)
agent = LlmAgent(
    name="summarizer_agent",
    model=settings.GEMINI_MODEL_SMART,
    description="Генерирует краткое саммари истории чата или документов",
    instruction="""You are a helpful assistant. 
Your goal is to summarize conversations or documents based on the user's request.

TOOLS:
- `fetch_chat_messages(chat_id, limit, since)`: Use this to get recent messages from a chat. `since` is an optional ISO datetime string to filter messages.
- `fetch_documents(chat_id, tags, limit)`: Use this to get documents from the knowledge base.

HOW TO WORK:
1. Identify what the user wants to summarize (chat history or documents).
2. Extract the `chat_id` from the context provided by the user.
3. Call the appropriate tool to get the content.
4. Summarize the content returned by the tool.
5. Provide a well-structured summary in markdown format.
6. Answer in the same language as the conversation/documents.
""",
    tools=[fetch_chat_messages, fetch_documents]
)

# Expose agent for ADK (ожидает root_agent)
root_agent = agent
