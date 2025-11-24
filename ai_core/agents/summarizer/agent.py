"""
Summarizer Agent

Агент для генерации саммари истории чата используя Google ADK.
"""

from google.adk.agents import LlmAgent

from ai_core.common.config import settings


# Создаём агента (один раз на уровне модуля)
agent = LlmAgent(
    name="summarizer_agent",
    model=settings.GEMINI_MODEL_SMART,
    description="Генерирует краткое саммари истории чата или документов",
    instruction="""You are a helpful assistant. 
Your goal is to summarize conversations or documents provided in the context.

HOW TO WORK:
1. Read the content provided in the user message (Chat History or Documents).
2. Summarize the content based on the user's request.
3. Provide a well-structured summary.
4. Answer in the same language as the conversation/documents.
""",
    tools=[]
)

# Expose agent for ADK (ожидает root_agent)
root_agent = agent
