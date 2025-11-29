"""Дружелюбный вывод результатов ADK eval.

Пример:
    PYTHONPATH=$(pwd) python scripts/adk_eval_utils/adk_eval_summary.py \
        --agent chat_observer \
        --history-dir ai_core/agents/chat_observer/.adk/eval_history \
        --eval-set chat_observer_fetch_messages_v1

Что показывает для каждого кейса:
- у агента спросили: <текст запроса>
- он ответил: <финальный ответ>
- это корректно / это ошибка! (по статусу кейса)
- какие инструменты вызывались
В конце — агрегированные метрики.
"""

import argparse
import glob
import json
import os
import re
import textwrap
from typing import Any, Dict, List, Tuple, Optional

FIELD_WIDTH = 26  # для выравнивания колонок


def load_latest_results(history_dir: str, agent: str, eval_set: str) -> Tuple[str, List[Tuple[Dict[str, Any], float]]]:
    # Pattern matching: agent_name + eval_set_id + timestamp + .evalset_result.json
    # Note: ADK uses the agent name from config or command line, and eval_set_id from the JSON.
    # We try a flexible pattern to catch files.
    pattern = os.path.join(
        history_dir, f"*{eval_set}*.evalset_result.json"
    )
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    if not files:
        # Fallback: try to find ANY file with the eval_set id in it
        pattern = os.path.join(history_dir, f"*{eval_set}*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime)
        
    if not files:
        raise FileNotFoundError(f"Не найдено файлов по шаблону {pattern} в {history_dir}")

    latest_file = files[-1]
    latest_mtime = os.path.getmtime(latest_file)

    # Берём все файлы, созданные в течение последних 2 минут от самого свежего.
    window_secs = 120
    latest_files = [
        p for p in files if latest_mtime - os.path.getmtime(p) <= window_secs
    ]

    results: List[Tuple[Dict[str, Any], float]] = []
    for path in latest_files:
        mtime = os.path.getmtime(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                data = json.loads(content)
                if isinstance(data, str):
                    data = json.loads(data)
                results.append((data, mtime))
        except Exception as e:
            print(f"⚠️ Ошибка чтения {path}: {e}")

    return latest_file, results


def _p(label: str, value: str) -> None:
    """Печатает строку с выравниванием по фиксированной ширине метки."""
    print(f"{label.ljust(FIELD_WIDTH)}{value}")


def extract_calls(invocation: Dict[str, Any]) -> List[str]:
    calls: List[str] = []
    interm = invocation.get("intermediate_data") or {}

    for call in interm.get("tool_uses", []) or []:
        name = call.get("name")
        args = call.get("args")
        if name:
            calls.append(f"{name} {args}")

    for event in interm.get("invocation_events", []) or []:
        for part in event.get("content", {}).get("parts", []) or []:
            fc = part.get("function_call")
            if fc:
                calls.append(f"{fc.get('name')} {fc.get('args')}")

    return calls


def count_steps(invocation: Dict[str, Any]) -> tuple[int, int]:
    """Возвращает (tool_calls_count, invocation_events_count)."""
    interm = invocation.get("intermediate_data") or {}
    tool_uses = interm.get("tool_uses") or []
    invocation_events = interm.get("invocation_events") or []
    return len(tool_uses), len(invocation_events)


def tool_score(case: Dict[str, Any]) -> Any:
    for metric in case.get("overall_eval_metric_results", []) or []:
        if metric.get("metric_name") == "tool_trajectory_avg_score":
            return metric.get("score")
    return None


def safe_final_text(invocation: Dict[str, Any]) -> str:
    final = invocation.get("final_response")
    if not final:
        return ""
    parts = final.get("parts") or []
    if not parts:
        return ""
    return parts[0].get("text", "") or ""


def _format_call(raw: str) -> str:
    # raw выглядит как "fetch_messages {'chat_id': 'id', 'limit': 3}"
    name, _, arg_str = raw.partition(" ")
    arg_str = arg_str.strip()
    if not arg_str:
        return name
    try:
        import ast

        args = ast.literal_eval(arg_str)
        if isinstance(args, dict):
            items = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
            return f"{name}({items})"
    except Exception:
        pass
    return raw


def expected_summary(case: Dict[str, Any]) -> Tuple[List[str], str]:
    invs = case.get("eval_metric_result_per_invocation", [])
    if not invs:
        return [], ""
    expected = invs[0].get("expected_invocation") or {}
    calls_raw = extract_calls(expected)
    calls = [_format_call(c) for c in calls_raw]
    resp = safe_final_text(expected)
    return calls, resp


def get_metrics(cases: List[Dict[str, Any]]) -> Dict[str, float]:
    """Extracts aggregated metrics from cases."""
    if not cases:
        return {}
    
    # Usually metrics are in the first case or aggregated separately.
    # Here we look at the first case's overall metrics as they often represent the set config/results
    metrics = {}
    for m in cases[0].get("overall_eval_metric_results", []) or []:
        name = m.get("metric_name")
        score = m.get("score")
        if name and score is not None:
            metrics[name] = float(score)
            
    # Calculate pass rate manually to be sure
    passed = sum(1 for c in cases if c.get("final_eval_status") == 1)
    total = len(cases)
    metrics["pass_rate"] = passed / total if total > 0 else 0.0
    
    return metrics


def print_summary(agent: str, history_dir: str, eval_set: str, width: int = 160) -> Dict[str, Any]:
    try:
        path, datasets = load_latest_results(history_dir, agent, eval_set)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return {"error": str(e)}

    print(f"Последний результат: {path}\n")

    # Дедублируем по eval_id, берём самый свежий кейс
    cases_by_id: Dict[str, Tuple[Dict[str, Any], float]] = {}
    for data, mtime in datasets:
        for case in data.get("eval_case_results", []):
            cid = case.get("eval_id") or f"unknown_{mtime}"
            prev = cases_by_id.get(cid)
            if (not prev) or (mtime > prev[1]):
                cases_by_id[cid] = (case, mtime)

    cases = [v[0] for v in cases_by_id.values()]

    passed = sum(1 for c in cases if c.get("final_eval_status") == 1)
    
    for case in cases:
        status_ok = case.get("final_eval_status") == 1
        status_str = "это корректно" if status_ok else "это ошибка!"
        inv = case.get("eval_metric_result_per_invocation", [])[0]["actual_invocation"]
        user_text = " ".join(
            p.get("text", "") for p in inv.get("user_content", {}).get("parts", []) or []
        ).replace("\n", " ")
        response = safe_final_text(inv)
        calls = extract_calls(inv)
        exp_calls, exp_resp = expected_summary(case)
        tool_steps, event_steps = count_steps(inv)

        response_clean = response.replace("\n", " ") if response else "(пусто)"
        exp_resp_clean = exp_resp.replace("\n", " ") if exp_resp else "не проверяется"

        exp_tools = "; ".join(exp_calls) if exp_calls else "не проверяется"
        act_tools = "; ".join(_format_call(c) for c in calls) if calls else "(нет вызовов)"

        print(f"Кейс: {case.get('eval_id')}")
        _p("вопрос:", textwrap.shorten(user_text, width=width))
        _p("ожид. ответ:", textwrap.shorten(exp_resp_clean, width=width))
        _p("факт. ответ:", textwrap.shorten(response_clean, width=width))
        _p("ожид. инструменты:", exp_tools)
        _p("факт. инструменты:", act_tools)
        metrics_list = case.get("overall_eval_metric_results", []) or []
        metrics_str = "; ".join(
            f"{m.get('metric_name')}={m.get('score')} (thr={m.get('threshold')})" for m in metrics_list
        ) or "—"

        _p("статус:", status_str)
        _p("метрики:", metrics_str)
        _p("шаги:", f"tool_calls={tool_steps}, invocation_events={event_steps}")
        print("-" * 80)

    metrics = get_metrics(cases)
    print("Итоговые метрики:")
    for k, v in metrics.items():
        print(f"- {k}: {v}")
        
    print(f"Итог: {passed} / {len(cases)} кейсов прошли")
    
    return {
        "passed": passed,
        "total": len(cases),
        "metrics": metrics,
        "file": path
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Короткий вывод ADK eval")
    parser.add_argument("--agent", default="chat_observer")
    parser.add_argument("--history-dir", required=True)
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--width", type=int, default=160, help="Макс. длина ответа")
    parser.add_argument("--json-summary", action="store_true", help="Вывести итоговый JSON в последней строке")
    args = parser.parse_args()

    summary = print_summary(args.agent, args.history_dir, args.eval_set, args.width)
    
    if args.json_summary:
        print("JSON_SUMMARY_START")
        print(json.dumps(summary))
        print("JSON_SUMMARY_END")


if __name__ == "__main__":
    main()
