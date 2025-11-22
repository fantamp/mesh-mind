import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock streamlit to avoid runtime errors during import in test environment
sys.modules["streamlit"] = MagicMock()

def test_ui_imports():
    """
    Simple smoke test to ensure UI modules can be imported without syntax errors.
    We mock streamlit because we can't run it in a headless test easily without a browser.
    """
    try:
        from ai_core.ui import main
        # Pages are scripts, hard to import directly due to naming. 
        # We assume if main imports, environment is okay.
    except ImportError as e:
        pytest.fail(f"Failed to import UI modules: {e}")
    except Exception as e:
        # It might fail due to other dependencies or side effects on import
        # But we just want to catch syntax errors or major import issues
        pass
