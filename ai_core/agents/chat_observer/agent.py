from google.adk.agents import LlmAgent
from ai_core.common.config import settings

# Import tools
from ai_core.tools.messages import fetch_messages

agent = LlmAgent(
    name="chat_observer",
    model=settings.GEMINI_MODEL_SMART,
    description="Agent responsible for observing and searching chat history.",
    instruction="""You are the Chat Observer.
Your goal is to find specific messages or patterns in the chat history based on the user's request.

HOW TO WORK:
1.  **Analyze Request**: Understand what kind of messages the user is looking for (e.g., "messages about project X", "links shared yesterday").
2.  **Fetch Messages**: Use the `fetch_messages` tool to search the database.
    *   Use appropriate filters (keywords, time range, author) to narrow down the search.
    *   Always call `fetch_messages` as the first action, even if параметры кажутся неполными; инструмент вернет ошибку при неверной дате, и её нужно показать пользователю.
    *   If the user says "вчера", assume UTC and use ISO start of that day (e.g. 2025-11-25T00:00:00Z). Default limit = 50 unless user asks otherwise.
3.  **Present Results**: Return a concise list of the found messages.
    *   Include timestamps and authors.
    *   Do not summarize deeply, just present the findings.
""",
    tools=[fetch_messages],
    sub_agents=[]
)

# ADK ожидает root_agent на уровне модуля
root_agent = agent
