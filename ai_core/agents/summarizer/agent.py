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
    instruction="""You are a helpful summarizer.
Your goal is to summarize the input.

HOW TO WORK:
1. Read the content provided in the input.
2. Summarize the content.
3. Provide a well-structured summary.
4. Answer in the same language as the input.
""",
    tools=[]
)
