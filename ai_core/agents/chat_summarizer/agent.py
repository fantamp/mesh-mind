from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from ai_core.common.config import settings

# Import tools and sub-agents
from ai_core.tools.messages import fetch_messages
from ai_core.agents.summarizer.agent import agent as simple_summarizer

# ============================================================================
# РЕШЕНИЯ ПО ПРОЕКТИРОВАНИЮ: Chat Summarizer Agent
# ============================================================================
# 
# 1. Использование инструментов (Tools):
#    - Использует `fetch_messages` для получения данных, а не полагается на контекст
#    - Использует `simple_summarizer` как под-агента (через AgentTool) для обработки текста
#
# 2. Stateless сессии (session_id = unique UUID):
#    - Каждая суммаризация независима
#    - Не требует хранения контекста предыдущих запросов
# ============================================================================
agent = LlmAgent(
    name="chat_summarizer",
    model=settings.GEMINI_MODEL_SMART,
    description="Agent responsible for summarizing chat history.",
    instruction="""You are the Chat Summarizer.
Your goal is to fetch relevant chat messages and produce a summary.

HOW TO WORK:
1.  **Fetch Messages**: Use the `fetch_messages` tool to retrieve chat history from the database.
    *   You can specify `limit`, `since` time, or other criteria.
    *   If the user didn't specify a range, default to the last 50 messages or use your judgment.
2.  **Summarize**: Once you have the messages, pass them to the `simple_summarizer` tool to generate a summary.
    
Do not try to summarize the text yourself as the tool is available.
""",
    tools=[
        fetch_messages, 
        AgentTool(agent=simple_summarizer.clone())],
)

# ADK ожидает root_agent на уровне модуля
root_agent = agent
