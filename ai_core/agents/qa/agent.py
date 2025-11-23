"""
QA Agent

Агент для ответов на вопросы на основе базы знаний (RAG pattern) используя Google ADK.
"""

import os
from google.adk.agents import LlmAgent

from ai_core.common.config import settings
from ai_core.tools.knowledge_base import search_knowledge_base

# Устанавливаем API key для ADK
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Создаём агента с инструментом поиска
_qa_agent = LlmAgent(
    name="qa_agent",
    model=settings.GEMINI_MODEL_SMART,
    description="Отвечает на вопросы пользователя на основе базы знаний",
    instruction="""You are a helpful AI assistant that answers questions based on a knowledge base.

HOW TO ANSWER:
1. You will be provided with a `chat_id` in the user's message (e.g., "CONTEXT: chat_id='...'").
2. ALWAYS call the `search_knowledge_base` tool first to find relevant information.
3. PASS THE EXACT `chat_id` to the `search_knowledge_base` tool.
4. The tool will return documents with sources. USE THESE DOCUMENTS to answer the question.
5. Extract the answer directly from the returned documents.
6. If the documents contain the answer, provide it with source citation.
7. ONLY say "Я не знаю" if the tool returns "No relevant information found in the knowledge base."

EXAMPLE:
User asks: "CONTEXT: chat_id='123' Question: What is the capital of Australia?"
Tool call: search_knowledge_base(query="capital of Australia", chat_id="123")
Tool returns: "[1] (source: telegram)\nThe capital of Australia is Canberra."
Your answer: "The capital of Australia is Canberra (source: telegram)."

Answer in the same language as the question.""",
    tools=[search_knowledge_base],  # Передаём custom tool
)

# Expose agent for ADK
agent = _qa_agent
