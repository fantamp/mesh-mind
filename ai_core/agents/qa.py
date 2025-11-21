"""
QA Agent

Агент для ответов на вопросы на основе базы знаний (RAG pattern) используя Google ADK.
"""

import asyncio
import os
import uuid
from typing import List, Dict, Any, Optional

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
# Note: _ResourceExhaustedError might be internal, relying on standard exceptions first
# from google.adk.models.google_llm import _ResourceExhaustedError 

from ai_core.common.config import settings
from ai_core.rag.vector_db import VectorDB

from ai_core.common.logging import logger

# Устанавливаем API key для ADK
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Инициализируем Vector Store (подключение к ChromaDB)
# Используем глобальную переменную для переиспользования соединения
_vector_store = VectorDB()

# Session service
_session_service = InMemorySessionService()


# Custom Tool: Поиск в базе знаний
def search_knowledge_base(query: str) -> str:
    """
    Ищет релевантную информацию в базе знаний (Vector DB) по запросу пользователя.
    Используй этот инструмент, когда пользователь задает вопрос, требующий фактической информации из документов.

    Args:
        query: Поисковый запрос пользователя. Должен быть сформулирован как поисковый запрос, а не как вопрос.

    Returns:
        Строка, содержащая найденные фрагменты текста с указанием источника.
    """
    logger.info(f"Поиск в базе знаний: {query}")
    
    try:
        # Ищем в векторной базе
        # VectorDB.search returns a dict with 'ids', 'documents', 'metadatas' (lists of lists)
        results = _vector_store.search(query, n_results=5)
        
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
    instruction="""You are a helpful AI assistant. Answer user questions based ONLY on the provided context 
from the knowledge base.

CRITICAL RULES:
1. You MUST use the `search_knowledge_base` tool to find relevant information before answering.
2. If the answer is not in the provided context, respond with "Я не знаю".
3. Do NOT hallucinate or make up information.
4. ALWAYS cite sources in the format: (источник: filename).
5. Provide clear and concise answers in the same language as the question.
""",
    tools=[search_knowledge_base],  # Передаём custom tool
)

# Создаём runner
_qa_runner = Runner(
    agent=_qa_agent,
    app_name="agents", # Используем "agents" для соответствия структуре ADK
    session_service=_session_service,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        ResourceExhausted, InternalServerError, ServiceUnavailable, Exception
    )),
    reraise=True
)
def ask_question(question: str, user_id: str = "default_user") -> str:
    """
    Задаёт вопрос QA агенту.
    
    Args:
        question: Вопрос пользователя
        user_id: ID пользователя (для session management)
        
    Returns:
        Ответ агента со ссылками на источники
        
    Raises:
        ValueError: Если вопрос пустой
        Exception: При ошибках вызова API
    """
    if not question or not question.strip():
        raise ValueError("Вопрос не может быть пустым")
    
    logger.info(f"Получен вопрос от {user_id}: {question}")
    
    try:
        # Формируем сообщение пользователя
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=question)]
        )
        
        # Генерируем session_id
        # В реальном приложении можно хранить маппинг user_id -> session_id
        # Для MVP создаем новую сессию или используем детерминированный ID, если хотим сохранять контекст
        # Здесь используем детерминированный ID для пользователя, чтобы сохранять контекст беседы
        session_id = f"qa_session_{user_id}"
        
        from concurrent.futures import ThreadPoolExecutor

        # Явно создаем сессию асинхронно перед использованием runner'а
        # ADK требует явного создания сессии
        def run_in_thread():
            try:
                asyncio.run(_session_service.create_session(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id
                ))
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
             # Если мы уже в event loop (например, в тестах), запускаем в отдельном потоке
            with ThreadPoolExecutor() as executor:
                executor.submit(run_in_thread).result()
        else:
            run_in_thread()
        
        # Вызываем агента через runner
        response_text = None
        
        # Runner.run возвращает генератор событий
        for event in _qa_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            # Ищем финальный ответ
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                break
        
        if not response_text:
            # Если не нашли final response, попробуем собрать из чанков (если стриминг)
            # Но для LlmAgent обычно есть final response event
            raise Exception("Агент не вернул ответ")
        
        logger.info(f"Ответ сгенерирован, длина: {len(response_text)} символов")
        return response_text
        
    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса: {e}")
        raise
