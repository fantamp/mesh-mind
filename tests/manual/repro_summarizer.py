import sys
from pathlib import Path
import datetime
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# We need to patch the Runner before importing summarizer, 
# but summarizer imports Runner at module level.
# So we will patch it where it is used or patch the class in the module.

from ai_core.common.models import DomainMessage
# Import summarizer - this will load the module and instantiate the agent/runner
from ai_core.services.agent_service import run_summarizer as summarize

def test_summarize():
    print("Testing summarize with Message object...")
    msg = DomainMessage(
        source="test",
        author_id="test_user",
        author_name="Test User",
        content="Hello world",
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    
    # Create a mock event for the runner response
    mock_event = MagicMock()
    mock_event.is_final_response.return_value = True
    mock_event.content.parts = [MagicMock(text="Summary generated successfully.")]
    
    # Patch the runner's run method on the INSTANCE used in the module
    # summarizer._summarizer_runner is the instance
    # Patch run_agent_sync in agent_service
    with patch('ai_core.services.agent_service.run_agent_sync', return_value="Summary generated successfully."):
        try:
            result = summarize(chat_id="test_chat", messages=[msg])
            print(f"Success! Result: {result}")
        except AttributeError as e:
            print(f"Failed with AttributeError: {e}")
            # Print traceback to see where it failed
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"Failed with {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_summarize()
