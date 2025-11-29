#!/usr/bin/env python3
import subprocess
import sys
import os
import json
from pathlib import Path

# Configuration
AGENTS = [
    {
        "name": "orchestrator",
        "path": "ai_core/agents/orchestrator",
        "eval_set": "tests/agents/eval/orchestrator/routing_eval.evalset.json",
        "config": "tests/agents/eval/orchestrator/test_config.json",
        "eval_set_id": "orchestrator_routing_v1"
    },
    {
        "name": "chat_summarizer",
        "path": "ai_core/agents/chat_summarizer",
        "eval_set": "tests/agents/eval/chat_summarizer/summarization_eval.evalset.json",
        "config": "tests/agents/eval/chat_summarizer/test_config.json",
        "eval_set_id": "chat_summarizer_eval_v1"
    },
    {
        "name": "chat_observer",
        "path": "ai_core/agents/chat_observer",
        "eval_set": "tests/agents/eval/chat_observer/fetch_messages_eval.evalset.json",
        "config": "tests/agents/eval/chat_observer/test_config.json",
        "eval_set_id": "chat_observer_fetch_messages_v1"
    }
]

def run_command(cmd, env=None, capture_output=False):
    """Runs a shell command and returns (success, output)."""
    print(f"Running: {cmd}")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, env=env, check=True, capture_output=True, text=True)
            return True, result.stdout
        else:
            subprocess.check_call(cmd, shell=True, env=env)
            return True, ""
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        return False, e.stdout if capture_output else ""

def main():
    project_root = os.getcwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root
    env["GEMINI_MODEL_SMART"] = "gemini-2.5-flash-lite" # Use fast model for evals

    print("🚀 Starting ADK Evaluation Suite...")
    
    # 1. Seed Database
    print("\n🌱 Seeding database...")
    if not run_command("python tests/agents/eval/seed_eval_db.py", env=env)[0]:
        sys.exit(1)

    results = {}

    # 2. Run Evals for each agent
    for agent in AGENTS:
        print(f"\n🤖 Evaluating Agent: {agent['name']}...")
        
        log_file = f"/tmp/adk_eval_{agent['name']}.log"
        cmd = f"adk eval {agent['path']} {agent['eval_set']} --config_file_path {agent['config']} > {log_file} 2>&1"
        
        success, _ = run_command(cmd, env=env)
        
        if success:
            print(f"✅ Eval finished for {agent['name']}")
            results[agent['name']] = {"status": "PASS", "metrics": {}}
        else:
            print(f"❌ Eval failed for {agent['name']}. Check logs: {log_file}")
            run_command(f"tail -n 20 {log_file}")
            results[agent['name']] = {"status": "FAIL", "metrics": {}}
            continue

        # 3. Print Summary and Capture Metrics
        history_dir = os.path.join(agent['path'], ".adk/eval_history")
        summary_cmd = f"python scripts/adk_eval_utils/adk_eval_summary.py --agent {agent['name']} --history-dir {history_dir} --eval-set {agent['eval_set_id']} --json-summary"
        
        # We want to see the output BUT also capture the JSON at the end.
        # So we run it, print stdout, and then parse the JSON part.
        success, output = run_command(summary_cmd, env=env, capture_output=True)
        print(output) # Show the human readable part
        
        if success:
            try:
                # Extract JSON between markers
                json_str = output.split("JSON_SUMMARY_START")[1].split("JSON_SUMMARY_END")[0].strip()
                summary_data = json.loads(json_str)
                results[agent['name']]["metrics"] = summary_data.get("metrics", {})
                
                # Check if all passed in summary
                if summary_data.get("passed") != summary_data.get("total"):
                     results[agent['name']]["status"] = "FAIL (Some cases failed)"
            except Exception as e:
                print(f"⚠️ Failed to parse summary metrics: {e}")

    # 4. Final Report
    print("\n" + "="*80)
    print("📊 FINAL EVALUATION REPORT")
    print("="*80)
    
    # Header
    print(f"{'Agent':<20} | {'Status':<20} | {'Pass Rate':<10} | {'Metrics'}")
    print("-" * 80)
    
    all_passed = True
    for name, data in results.items():
        status = data["status"]
        metrics = data["metrics"]
        pass_rate = f"{metrics.get('pass_rate', 0)*100:.0f}%"
        
        # Format other metrics
        metric_str = ", ".join(f"{k}={v:.2f}" for k, v in metrics.items() if k != "pass_rate")
        
        icon = "✅" if "PASS" in status else "❌"
        print(f"{icon} {name:<17} | {status:<20} | {pass_rate:<10} | {metric_str}")
        
        if "PASS" not in status:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All agents passed evaluation!")
        sys.exit(0)
    else:
        print("\n⚠️ Some agents failed evaluation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
