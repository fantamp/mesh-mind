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
    instruction="""You are the main Orchestrator for the Mesh Mind system.
Your goal is to understand the user's request and route it to the appropriate sub-agent.

AVAILABLE SUB-AGENTS:
1. **chat_summarizer**: Use for requests to summarize chat history or conversations.
2. **chat_observer**: Use for finding specific messages AND for answering general questions.
3. **maintenance_agent**: Use for administrative tasks like updating the bot, restarting the server, or checking logs.

ROUTING LOGIC:
- If the user asks for a summary of the chat, delegate to `chat_summarizer`.
- If the user asks a question OR wants to find specific messages, delegate to `chat_observer`.
    - Examples: "What is X?", "Find messages from @user", "Help me with Python".
- If the user asks to update, restart, or check logs, delegate to `maintenance_agent`.
    - Examples: "Update the bot", "Restart server", "Show me the logs".

SILENT MODE:
- If the user's message does not contain a direct question, a request for summary, or specific keywords triggering an action, but it is a voice message, then return a very short, 1-2 sentence summary of the message's meaning in the format "The voice message was about..." using the language of the user.
- Do not respond to casual conversation unless explicitly addressed.

Always delegate the task if a sub-agent is suitable.
""",
    sub_agents=[
        chat_summarizer, 
        chat_observer,
        maintenance_agent
    ] 
)
root_agent = agent  # ADK ищет root_agent
