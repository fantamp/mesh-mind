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
4. **chat_observer**: Use for finding specific messages. For example, "Give me 10 messages from yesterday" or "Give me 10 messages from @user".

ROUTING LOGIC:
- If the user asks for a summary of the chat, delegate to `chat_summarizer`.
- If the user asks for a summary of a document, delegate to `doc_summarizer`.
- If the user asks a question, delegate to `qa_agent`. Allmost all requests with question mark are questions, so you have to delegate to `qa_agent`.
- If the user wants to find specific messages, delegate to `chat_observer`. Only requests ends with dot are accepteble for `chat_observer`.

SILENT MODE:
- If the user's message does not contain a direct question, a request for summary, or specific keywords triggering an action, and is just a general chat message not addressed to you, you MUST return "null" (string) or an empty response.
- Do not respond to casual conversation unless explicitly addressed.

Always delegate the task if a sub-agent is suitable.
""",
    sub_agents=[
        chat_summarizer, 
        doc_summarizer.clone(), 
        qa_agent, 
        chat_observer
    ] 
)
root_agent = agent  # ADK ищет root_agent
