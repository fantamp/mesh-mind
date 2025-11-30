import unittest
from unittest.mock import patch, MagicMock
from ai_core.agents.maintenance_agent.tools import check_version_status

class TestVersionCheck(unittest.TestCase):
    @patch('subprocess.run')
    def test_version_up_to_date(self, mock_run):
        # Mock git fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0
        
        # Mock git status
        mock_status = MagicMock()
        mock_status.stdout = "On branch main\nYour branch is up to date with 'origin/main'.\nnothing to commit, working tree clean"
        
        # Mock git rev-parse
        mock_branch = MagicMock()
        mock_branch.stdout = "main"
        
        # Mock git log
        mock_log = MagicMock()
        mock_log.stdout = ""
        
        mock_run.side_effect = [mock_fetch, mock_status, mock_branch, mock_log]
        
        result = check_version_status()
        self.assertIn("Up to date with remote", result)
        self.assertIn("**Branch:** main", result)

    @patch('subprocess.run')
    def test_version_behind(self, mock_run):
        # Mock git fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0
        
        # Mock git status
        mock_status = MagicMock()
        mock_status.stdout = "On branch main\nYour branch is behind 'origin/main' by 2 commits."
        
        # Mock git rev-parse
        mock_branch = MagicMock()
        mock_branch.stdout = "main"
        
        # Mock git log
        mock_log = MagicMock()
        mock_log.stdout = "a1b2c3d Fix bug\ne5f6g7h Add feature"
        
        mock_run.side_effect = [mock_fetch, mock_status, mock_branch, mock_log]
        
        result = check_version_status()
        self.assertIn("Behind by 2 commits", result)
        self.assertIn("Fix bug", result)

    @patch('subprocess.run')
    def test_local_changes(self, mock_run):
        # Mock git fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0
        
        # Mock git status
        mock_status = MagicMock()
        mock_status.stdout = "On branch main\nChanges not staged for commit:\n  modified: file.py"
        
        # Mock git rev-parse
        mock_branch = MagicMock()
        mock_branch.stdout = "main"
        
        # Mock git log
        mock_log = MagicMock()
        mock_log.stdout = ""
        
        mock_run.side_effect = [mock_fetch, mock_status, mock_branch, mock_log]
        
        result = check_version_status()
        self.assertIn("Local Changes Detected", result)

if __name__ == '__main__':
    unittest.main()
