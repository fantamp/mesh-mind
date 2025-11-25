from google.adk.agents import LlmAgent
from ai_core.common.config import settings

# Import sub-agents
from ai_core.agents.chat_summarizer.agent import agent as chat_summarizer
from ai_core.agents.summarizer.agent import agent as doc_summarizer
from ai_core.agents.qa.agent import agent as qa_agent
from ai_core.agents.chat_observer.agent import agent as chat_observer

agent = LlmAgent(
    name="orchestrator",
    model=settings.GEMINI_MODEL_SMART,
    description="Orchestrator agent that routes user requests to specialized sub-agents.",
    instruction="""You are the main Orchestrator for the Mesh Mind system.
Your goal is to understand the user's request and route it to the appropriate sub-agent.

AVAILABLE SUB-AGENTS:
1. **chat_summarizer**: Use for requests to summarize chat history or conversations.
2. **doc_summarizer**: Use for requests to summarize specific documents.
3. **qa_agent**: Use for answering questions based on the knowledge base or general knowledge.
4. **chat_observer**: Use for finding specific messages, searching chat history, or observing chat activity.

ROUTING LOGIC:
- If the user asks for a summary of the chat, delegate to `chat_summarizer`.
- If the user asks for a summary of a document, delegate to `doc_summarizer`.
- If the user asks a question, delegate to `qa_agent`.
- If the user wants to find specific messages or check chat history, delegate to `chat_observer`.

Always delegate the task; do not attempt to answer directly unless it's a simple greeting or clarification.
""",
    sub_agents=[
        chat_summarizer, 
        doc_summarizer.clone(), 
        qa_agent, 
        chat_observer
    ] 
)
root_agent = agent  # ADK ищет root_agent
