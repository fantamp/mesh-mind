"""
QA Agent

Агент для ответов на вопросы на основе базы знаний (RAG pattern) используя Google ADK.
"""

import os
import contextvars
from typing import Optional

from google.adk.agents import LlmAgent

from ai_core.common.config import settings
from ai_core.rag.vector_db import VectorDB
from ai_core.common.logging import logger
from ai_core.common.adk import run_agent_sync, standard_retry

# Устанавливаем API key для ADK
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Инициализируем Vector Store (подключение к ChromaDB)
# Используем глобальную переменную для переиспользования соединения
_vector_store = VectorDB()

# Context variable for chat_id
_chat_id_ctx = contextvars.ContextVar("chat_id", default=None)

# Custom Tool: Поиск в базе знаний
def search_knowledge_base(query: str, chat_id: str) -> str:
    """
    Ищет релевантную информацию в базе знаний (Vector DB) по запросу пользователя.
    Используй этот инструмент, когда пользователь задает вопрос, требующий фактической информации из документов.

    Args:
        query: Поисковый запрос пользователя. Должен быть сформулирован как поисковый запрос, а не как вопрос.
        chat_id: ID чата для фильтрации поиска.

    Returns:
        Строка, содержащая найденные фрагменты текста с указанием источника.
    """
    logger.info(f"Поиск в базе знаний: {query} (chat_id={chat_id})")
    
    try:
        # Ищем в векторной базе
        # VectorDB.search returns a dict with 'ids', 'documents', 'metadatas' (lists of lists)
        results = _vector_store.search(query, n_results=5, chat_id=chat_id)
        
        if not results or not results.get('documents') or not results['documents'][0]:
            return "В базе знаний не найдено релевантной информации по этому запросу."
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        # Форматируем результаты
        formatted_results = []
        for idx, (text, metadata) in enumerate(zip(documents, metadatas), 1):
            source = metadata.get("source", "unknown")
            # Можно добавить другие метаданные, если есть (например, номер страницы)
            formatted_results.append(f"[{idx}] (источник: {source})\n{text}")
        
        output = "\n\n".join(formatted_results)
        logger.debug(f"Найдено {len(documents)} результатов")
        return output
        
    except Exception as e:
        logger.error(f"Ошибка при поиске в базе знаний: {e}")
        return f"Ошибка поиска: {str(e)}"


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
7. ONLY say "Я не знаю" if the tool returns "В базе знаний не найдено релевантной информации".

EXAMPLE:
User asks: "CONTEXT: chat_id='123' Question: What is the capital of Australia?"
Tool call: search_knowledge_base(query="capital of Australia", chat_id="123")
Tool returns: "[1] (источник: telegram)\nThe capital of Australia is Canberra."
Your answer: "The capital of Australia is Canberra (источник: telegram)."

Answer in the same language as the question.""",
    tools=[search_knowledge_base],  # Передаём custom tool
)


@standard_retry
def ask_question(question: str, user_id: str = "default_user", chat_id: str = None) -> str:
    """
    Задаёт вопрос QA агенту.
    
    Args:
        question: Вопрос пользователя
        user_id: ID пользователя (для session management)
        chat_id: ID чата для фильтрации контекста
        
    Returns:
        Ответ агента со ссылками на источники
        
    Raises:
        ValueError: Если вопрос пустой
        Exception: При ошибках вызова API
    """
    if not question or not question.strip():
        raise ValueError("Вопрос не может быть пустым")
    
    logger.info(f"Получен вопрос от {user_id} (chat_id={chat_id}): {question}")
    
    # Формируем сообщение пользователя с контекстом
    context_prefix = f"CONTEXT: chat_id='{chat_id}'\n" if chat_id else "CONTEXT: chat_id=None\n"
    full_question = context_prefix + "Question: " + question
    
    # Генерируем session_id
    # В реальном приложении можно хранить маппинг user_id -> session_id
    # Для MVP создаем новую сессию или используем детерминированный ID, если хотим сохранять контекст
    # Здесь используем детерминированный ID для пользователя, чтобы сохранять контекст беседы
    session_id = f"qa_session_{user_id}"
    
    # Используем shared helper
    return run_agent_sync(
        agent=_qa_agent,
        user_message=full_question,
        user_id=user_id,
        session_id=session_id
    )
