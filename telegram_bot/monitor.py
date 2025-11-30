# See docs/features/new-commit-notify.md for more details
import subprocess
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class CommitMonitor:
    def __init__(self):
        self.current_branch = self._get_current_branch()
        # Initialize last_seen_hash with the current remote tip to avoid notifying about old pending commits on startup
        self._fetch()
        self.last_seen_hash = self._get_remote_tip()
        logger.info(f"CommitMonitor initialized. Branch: {self.current_branch}, Last seen: {self.last_seen_hash}")

    def _run_git(self, args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                logger.error(f"Git command failed: git {' '.join(args)}\n{result.stderr}")
                return ""
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Exception running git: {e}")
            return ""

    def _get_current_branch(self) -> str:
        return self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "main"

    def _fetch(self):
        self._run_git(["fetch"])

    def _get_remote_tip(self) -> str:
        return self._run_git(["rev-parse", f"origin/{self.current_branch}"])

    def check_for_updates(self) -> List[str]:
        """
        Checks for new commits on the remote branch since the last check.
        Returns a list of new commit messages (oneline format).
        """
        self._fetch()
        current_remote_hash = self._get_remote_tip()

        if not current_remote_hash:
            return []

        if not self.last_seen_hash:
            # Should not happen if init worked, but recover by setting it
            self.last_seen_hash = current_remote_hash
            return []

        if current_remote_hash == self.last_seen_hash:
            return []

        # Get commits between last seen and current remote tip
        # Format: "hash message"
        commits_output = self._run_git([
            "log", 
            f"{self.last_seen_hash}..{current_remote_hash}", 
            "--oneline"
        ])
        
        self.last_seen_hash = current_remote_hash
        
        if not commits_output:
            return []
            
        return commits_output.split('\n')
