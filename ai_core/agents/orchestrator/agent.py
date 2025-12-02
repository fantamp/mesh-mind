from google.adk.agents import LlmAgent
from ai_core.common.config import settings

# Import sub-agents
from ai_core.agents.chat_summarizer.agent import agent as chat_summarizer
from ai_core.agents.canvas_manager.agent import agent as canvas_manager
from ai_core.agents.maintenance_agent.agent import agent as maintenance_agent
from ai_core.agents.walt_disney.facilitator import agent as disney_facilitator

agent = LlmAgent(
    name="orchestrator",
    model=settings.GEMINI_MODEL_SMART,
    description="Orchestrator agent that routes user requests to specialized sub-agents.",
    instruction="""You are the "Mesh Mind" system's Orchestrator.
Goal: Route user requests to specialized sub-agents.

RULES:
0. AUTHORIZATION: Always ensure the user has provided integer chat_id to pass it to the tools/sub-agents before delegating any task.
1. DELEGATION: If a sub-agent is suitable, delegate the task immediately.
2. FALLBACK (if no sub-agent fits):
    - Voice Messages (identified by "Media type: voice"): Provide a concise 1-2 sentence summary in the user's language.
    - Direct Questions: Answer them.
    - Otherwise: Keep silent.

AVAILABLE AGENTS:
- `chat_summarizer`: For summarizing chat history.
- `canvas_manager`: For general canvas organization and observation.
- `maintenance_agent`: For system maintenance and debugging.
- `disney_facilitator`: For creative problem solving, brainstorming, and planning using the Walt Disney Strategy (Dreamer, Realist, Critic). Use this when the user wants to "brainstorm", "plan a project", "develop an idea", or specifically mentions "Disney strategy".
""",
    sub_agents=[
        chat_summarizer, 
        canvas_manager,
        maintenance_agent,
        disney_facilitator
    ] 
)
root_agent = agent  # ADK ищет root_agent
