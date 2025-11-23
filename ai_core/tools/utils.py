import asyncio
from typing import TypeVar, Coroutine, Any
from concurrent.futures import ThreadPoolExecutor

T = TypeVar("T")

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
