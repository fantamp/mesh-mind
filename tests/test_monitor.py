import unittest
from unittest.mock import patch, MagicMock
from telegram_bot.monitor import CommitMonitor

class TestCommitMonitor(unittest.TestCase):
    @patch('telegram_bot.monitor.CommitMonitor._run_git')
    def test_init_fetches_and_sets_last_seen(self, mock_run_git):
        # Setup mocks
        mock_run_git.side_effect = [
            "main",         # _get_current_branch -> rev-parse --abbrev-ref HEAD
            "",             # _fetch -> fetch
            "hash_init"     # _get_remote_tip -> rev-parse origin/main
        ]
        
        monitor = CommitMonitor()
        
        self.assertEqual(monitor.current_branch, "main")
        self.assertEqual(monitor.last_seen_hash, "hash_init")
        self.assertEqual(mock_run_git.call_count, 3)

    @patch('telegram_bot.monitor.CommitMonitor._run_git')
    def test_check_for_updates_no_change(self, mock_run_git):
        # Setup init mocks
        mock_run_git.side_effect = ["main", "", "hash_old"]
        monitor = CommitMonitor()
        
        # Reset mock for check_for_updates
        mock_run_git.reset_mock()
        mock_run_git.side_effect = [
            "",             # _fetch
            "hash_old"      # _get_remote_tip (same as last seen)
        ]
        
        updates = monitor.check_for_updates()
        self.assertEqual(updates, [])
        self.assertEqual(monitor.last_seen_hash, "hash_old")

    @patch('telegram_bot.monitor.CommitMonitor._run_git')
    def test_check_for_updates_with_new_commits(self, mock_run_git):
        # Setup init mocks
        mock_run_git.side_effect = ["main", "", "hash_old"]
        monitor = CommitMonitor()
        
        # Reset mock for check_for_updates
        mock_run_git.reset_mock()
        mock_run_git.side_effect = [
            "",             # _fetch
            "hash_new",     # _get_remote_tip (changed)
            "hash_new New commit 2\nhash_mid New commit 1" # git log output
        ]
        
        updates = monitor.check_for_updates()
        
        self.assertEqual(len(updates), 2)
        self.assertIn("New commit 2", updates[0])
        self.assertEqual(monitor.last_seen_hash, "hash_new")
        
        # Verify git log call arguments
        call_args = mock_run_git.call_args_list[2]
        self.assertIn("hash_old..hash_new", call_args[0][0])

if __name__ == '__main__':
    unittest.main()
