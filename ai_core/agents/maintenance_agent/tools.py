import subprocess
import sys
import os
from ai_core.common.config import settings

def update_codebase() -> str:
    """
    Updates the codebase from the remote repository using git pull.
    Only works in production environment.
    """
    if settings.ENV != "prod":
        return "SKIPPED: Not in production environment. Update skipped."
    
    try:
        result = subprocess.run(
            ["git", "pull"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode == 0:
            return f"SUCCESS: Codebase updated.\n{result.stdout}"
        else:
            return f"ERROR: Git pull failed.\n{result.stderr}"
    except Exception as e:
        return f"ERROR: Exception during update: {str(e)}"

def restart_application() -> str:
    """
    Restarts the application by exiting the current process.
    Relies on an external loop wrapper to restart the process.
    Only works in production environment.
    """
    if settings.ENV != "prod":
        return "SKIPPED: Not in production environment. Restart skipped."
    
    # Flush stdout/stderr to ensure logs are written
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("Initiating restart via Maintenance Agent...")
    os._exit(0)
    # Unreachable code
    return "Restarting..." 

def get_recent_logs(lines: int = 50) -> str:
    """
    Retrieves the last N lines of the application log.
    """
    log_file = "mesh-mind.log"
    # Try to find log file in current or parent directories if not found
    if not os.path.exists(log_file):
        # Fallback to project root if running from subdirectory
        root_log = os.path.join(settings.PROJECT_ROOT, "mesh-mind.log")
        if os.path.exists(root_log):
            log_file = root_log
        else:
            return f"ERROR: Log file '{log_file}' not found."
    
    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), log_file],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"ERROR: Could not read logs.\n{result.stderr}"
    except Exception as e:
        return f"ERROR: Exception reading logs: {str(e)}"

def check_version_status() -> str:
    """
    Checks the current version status of the codebase.
    Returns information about local changes and pending updates from remote.
    """
    try:
        # 1. Fetch latest info from remote
        fetch_result = subprocess.run(
            ["git", "fetch"],
            capture_output=True,
            text=True,
            check=False
        )
        if fetch_result.returncode != 0:
            return f"ERROR: Git fetch failed.\n{fetch_result.stderr}"

        # 2. Check for local changes
        status_result = subprocess.run(
            ["git", "status", "-uno"],
            capture_output=True,
            text=True,
            check=False
        )
        local_status = status_result.stdout.strip()
        
        # 3. Check for pending commits (behind remote)
        # Assumes 'origin' is the remote and the current branch tracks an upstream
        # getting current branch name
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        current_branch = branch_result.stdout.strip()
        
        commits_result = subprocess.run(
            ["git", "log", f"HEAD..origin/{current_branch}", "--oneline"],
            capture_output=True,
            text=True,
            check=False
        )
        pending_commits = commits_result.stdout.strip()
        
        report = []
        report.append(f"**Branch:** {current_branch}")
        
        if "Your branch is up to date" in local_status:
             report.append("✅ **Status:** Up to date with remote.")
        elif pending_commits:
             count = len(pending_commits.split('\n'))
             report.append(f"⚠️ **Status:** Behind by {count} commits.")
        else:
             report.append("ℹ️ **Status:** Local state differs (possibly ahead or diverged).")

        if pending_commits:
            report.append("\n**Pending Updates:**")
            report.append(pending_commits)
            
        if "Changes not staged for commit" in local_status or "Changes to be committed" in local_status:
            report.append("\n⚠️ **Local Changes Detected:**")
            report.append("There are uncommitted local changes on the server.")

        return "\n".join(report)

    except Exception as e:
        return f"ERROR: Exception checking version: {str(e)}"
