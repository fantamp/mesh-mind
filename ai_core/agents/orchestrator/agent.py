from google.adk.agents import LlmAgent
from ai_core.common.config import settings

# Import sub-agents
from ai_core.agents.chat_summarizer.agent import agent as chat_summarizer
from ai_core.agents.canvas_manager.agent import agent as canvas_manager
from ai_core.agents.maintenance_agent.agent import agent as maintenance_agent

agent = LlmAgent(
    name="orchestrator",
    model=settings.GEMINI_MODEL_SMART,
    description="Orchestrator agent that routes user requests to specialized sub-agents.",
    instruction="""You are the Mesh Mind Orchestrator.
Goal: Route user requests to specialized sub-agents.

RULES:
1. DELEGATION: If a sub-agent is suitable, delegate the task immediately.
2. FALLBACK (if no sub-agent fits):
    - Voice Messages (identified by "Media type: voice"): Provide a concise 1-2 sentence summary in the user's language.
    - Direct Questions: Answer them.
    - Otherwise: Keep silent.
""",
    sub_agents=[
        chat_summarizer, 
        canvas_manager,
        maintenance_agent
    ] 
)
root_agent = agent  # ADK ищет root_agent
