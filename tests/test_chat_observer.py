import pytest
from unittest.mock import MagicMock, AsyncMock
from ai_core.agents.chat_observer.agent import agent

@pytest.mark.asyncio
async def test_chat_observer_instruction():
    """Test that chat observer has correct instruction and tools."""
    assert "Chat Observer" in agent.instruction
    # assert "QA Agent" in agent.instruction # REMOVED: Instruction changed
    # Check if tool is in the list (it might be a function or a Tool object)
    tool_names = [t.__name__ if hasattr(t, "__name__") else t.name for t in agent.tools]
    assert "fetch_messages" in tool_names

@pytest.mark.asyncio
async def test_chat_observer_tools():
    """Test that fetch_messages tool is available."""
    tool_names = [t.__name__ if hasattr(t, "__name__") else t.name for t in agent.tools]
    assert "fetch_messages" in tool_names
