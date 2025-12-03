import asyncio
import functools
import logging
import os
from google.adk.tools import ToolContext
from typing import TypeVar, Coroutine, Any, Callable

from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

T = TypeVar("T")

def log_tool_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to log tool calls with smart truncation of long string arguments.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Helper to process values
        def process_val(v):
            if isinstance(v, str) and len(v) > 100:
                return v[:100] + "..."
            return v

        # Process args and kwargs for logging
        log_args = [process_val(a) for a in args]
        log_kwargs = {k: process_val(v) for k, v in kwargs.items()}
        
        logger.info(f"Tool Call: {func.__name__} | Args: {log_args} | Kwargs: {log_kwargs}")
        
        result = func(*args, **kwargs)
        
        # Log result
        log_result = process_val(result)
        logger.info(f"Tool Result: {func.__name__} | Result: {log_result}")
        
        return result
    return wrapper

def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Runs an async coroutine from a synchronous context.
    Handles cases where an event loop is already running.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If we are in a running loop (e.g. inside a tool called by an async agent runner),
        # we can't just use asyncio.run().
        # However, ADK tools are often called synchronously.
        # If the caller is async but calls this sync tool, we might block the loop if we are not careful.
        # But here we assume we need to bridge sync -> async.
        # Ideally, we should use a thread to run the async code if we are already in a loop
        # to avoid "This event loop is already running" error.
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def extract_chat_id(tool_context: ToolContext) -> int:
    chat_id = tool_context.state.get("chat_id")
    
    if not chat_id:
        chat_id = os.getenv("CHAT_ID")
    if not chat_id:
        raise ValueError("Access denied: Chat ID not found in tool context state or environment variables")
    return int(chat_id)
