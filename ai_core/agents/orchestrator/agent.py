from google.adk.agents import LlmAgent
from ai_core.common.config import settings

# Import sub-agents
from ai_core.agents.chat_summarizer.agent import agent as chat_summarizer
from ai_core.agents.chat_observer.agent import agent as chat_observer
from ai_core.agents.maintenance_agent.agent import agent as maintenance_agent

# ============================================================================
# РЕШЕНИЯ ПО ПРОЕКТИРОВАНИЮ: Orchestrator Agent
# ============================================================================
# 
# 1. Мульти-агентный подход через sub_agents:
#    - Позволяет делегировать задачи на основе намерений (intent) на естественном языке
#    - Избегает хрупкого сопоставления по ключевым словам (например, if/else)
#    - Оркестратор анализирует запрос пользователя и направляет его специализированному агенту
#
# 2. Тихий режим:
#    - Отвечает только на прямые вопросы/команды
#
# 3. Повторное использование сессии (session_id = chat_id):
#    - InMemorySessionService сохраняет контекст разговора для каждого чата
#    - Обеспечивает многоходовые взаимодействия без потери истории
# ============================================================================
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
        chat_observer,
        maintenance_agent
    ] 
)
root_agent = agent  # ADK ищет root_agent
