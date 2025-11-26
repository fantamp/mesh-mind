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
from typing import Any, Dict, List, Tuple

FIELD_WIDTH = 26  # для выравнивания колонок


def load_latest_results(history_dir: str, agent: str, eval_set: str) -> Tuple[str, List[Tuple[Dict[str, Any], float]]]:
    pattern = os.path.join(
        history_dir, f"{agent}_{eval_set}_*.evalset_result.json"
    )
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    if not files:
        raise FileNotFoundError(f"Не найдено файлов по шаблону {pattern}")

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
        content = open(path, "r", encoding="utf-8").read()
        data = json.loads(content)
        if isinstance(data, str):
            data = json.loads(data)
        results.append((data, mtime))

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Короткий вывод ADK eval")
    parser.add_argument("--agent", default="chat_observer")
    parser.add_argument("--history-dir", required=True)
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--width", type=int, default=160, help="Макс. длина ответа")
    args = parser.parse_args()

    path, datasets = load_latest_results(args.history_dir, args.agent, args.eval_set)
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
    failed = len(cases) - passed

    for case in cases:
        status_ok = case.get("final_eval_status") == 1
        status_str = "это корректно" if status_ok else "это ошибка!"
        inv = case.get("eval_metric_result_per_invocation", [])[0]["actual_invocation"]
        user_text = " ".join(
            p.get("text", "") for p in inv.get("user_content", {}).get("parts", []) or []
        ).replace("\n", " ")
        response = safe_final_text(inv)
        calls = extract_calls(inv)
        tscore = tool_score(case)
        exp_calls, exp_resp = expected_summary(case)
        tool_steps, event_steps = count_steps(inv)

        response_clean = response.replace("\n", " ") if response else "(пусто)"
        exp_resp_clean = exp_resp.replace("\n", " ") if exp_resp else "не проверяется"

        exp_tools = "; ".join(exp_calls) if exp_calls else "не проверяется"
        act_tools = "; ".join(_format_call(c) for c in calls) if calls else "(нет вызовов)"

        print(f"Кейс: {case.get('eval_id')}")
        _p("вопрос:", user_text)
        _p("ожид. ответ:", textwrap.shorten(exp_resp_clean, width=args.width))
        _p("факт. ответ:", textwrap.shorten(response_clean, width=args.width))
        _p("ожид. инструменты:", exp_tools)
        _p("факт. инструменты:", act_tools)
        metrics = case.get("overall_eval_metric_results", []) or []
        metrics_str = "; ".join(
            f"{m.get('metric_name')}={m.get('score')} (thr={m.get('threshold')})" for m in metrics
        ) or "—"

        _p("статус:", status_str)
        _p("метрики:", metrics_str)
        _p("шаги:", f"tool_calls={tool_steps}, invocation_events={event_steps}")
        print("-" * 80)

    # Итоговые метрики (берём из первого кейса, обычно одинаковые правила)
    if cases:
        metrics = cases[0].get("overall_eval_metric_results", []) or []
        print("Итоговые метрики:")
        for m in metrics:
            print(f"- {m.get('metric_name')}: threshold={m.get('threshold')} score={m.get('score')}")
    print(f"Итог: {passed} / {len(cases)} кейсов прошли")


if __name__ == "__main__":
    main()
