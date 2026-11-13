"""Run the post-freeze deliberation budget control for LXAI 2026.

This control repeats ONLY the deliberative arm of the clean symmetric clause-order
factorial with a larger output budget.  States, language strings, clause order,
models, temperature, seed, transport, parser and scoring remain unchanged.

Unlike the original factorial runner, this runner also records Ollama termination
metadata (done_reason, eval_count, prompt_eval_count, durations) so budget
exhaustion can be diagnosed directly rather than inferred from response length.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import random
from time import perf_counter
from typing import Any, Sequence

import run_experiment as base
from direct_ollama_client import DirectOllamaChatClient
from game.replay_engine import parse_model_response
from game.research_runtime import extract_response_text
from run_deliberation_control import SYSTEM_PROMPT as DELIBERATION_SYSTEM_PROMPT, extract_final_command
from run_symmetric_clause_order_factorial import (
    A_COMMAND,
    B_COMMAND,
    LANGUAGE_LABELS,
    LANGUAGES,
    ORDERS,
    collect_provenance,
    render_policy,
    selected_cases,
)

HERE = Path(__file__).resolve().parent


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LXAI deliberation output-budget control.")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--languages", nargs="+", choices=LANGUAGES, default=list(LANGUAGES))
    parser.add_argument("--orders", nargs="+", choices=ORDERS, default=list(ORDERS))
    parser.add_argument("--suite", type=Path, default=HERE / "suite_decision_complexity.json")
    parser.add_argument("--host", default="http://localhost")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--order-seed", type=int, default=20260825)
    parser.add_argument("--num-predict", type=int, default=1024)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    models = [m.strip() for m in args.models if m.strip()]
    suite_payload, cases, policy_by_case = selected_cases(args.suite)
    rules = base.rules()
    base.validate_suite(cases, rules)

    cells: list[tuple[str, int, base.TrialCase, str, str]] = []
    for model_index, model in enumerate(models):
        rng = random.Random(args.order_seed + model_index)
        groups = [
            (repeat, case, language, order)
            for repeat in range(args.repeats)
            for case in cases
            for language in args.languages
            for order in args.orders
        ]
        rng.shuffle(groups)
        cells.extend((model, *group) for group in groups)

    print(f"Semantic states: {len(cases)}")
    print(f"Models: {', '.join(models)}")
    print(f"Languages: {', '.join(args.languages)}")
    print(f"Orders: {', '.join(args.orders)}")
    print(f"Deliberative num_predict: {args.num_predict}")
    print(f"Planned model calls: {len(cells)}")
    if args.dry_run:
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or HERE / "controls" / "deliberation_budget" / stamp
    output.mkdir(parents=True, exist_ok=True)

    metadata = {
        "experiment": "LXAI 2026 deliberation output-budget post-freeze control",
        "relation_to_symmetric_factorial": (
            "Repeats the deliberative cells of the clean symmetric clause-order factorial "
            "with larger num_predict and records Ollama termination metadata."
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "languages": args.languages,
        "language_labels": LANGUAGE_LABELS,
        "orders": args.orders,
        "n_semantic_states": len(cases),
        "n_invocations_planned": len(cells),
        "repeats": args.repeats,
        "temperature": args.temperature,
        "seed": args.seed,
        "order_seed": args.order_seed,
        "num_predict": args.num_predict,
        "source_suite": str(args.suite),
        "source_suite_version": suite_payload.get("version"),
        "system_prompt": DELIBERATION_SYSTEM_PROMPT,
        "provenance": collect_provenance(models, args.host, args.port, args.suite),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    client = DirectOllamaChatClient(host=args.host, port=args.port)
    rows: list[dict[str, Any]] = []
    with (output / "results.jsonl").open("w", encoding="utf-8") as jsonl:
        for index, (model, repeat, case, language, order) in enumerate(cells, 1):
            policy_id = policy_by_case[case.case_id]
            instruction = render_policy(policy_id, language, order)
            trial_case = replace(case, variants={language: instruction})
            messages = [
                {"role": "system", "content": DELIBERATION_SYSTEM_PROMPT},
                {"role": "user", "content": base.user_message(trial_case, language)},
            ]
            options = {
                "temperature": args.temperature,
                "seed": args.seed + repeat,
                "num_predict": args.num_predict,
            }
            started = perf_counter()
            try:
                response = client.chat(model=model, messages=messages, options=options, stream=False)
                full_response = extract_response_text(response)
                latency_ms = (perf_counter() - started) * 1000.0
                provider_error = None
            except Exception as exc:
                response = {}
                full_response = ""
                latency_ms = (perf_counter() - started) * 1000.0
                provider_error = f"{type(exc).__name__}: {exc}"

            extraction_error = None
            scored_response = full_response
            if provider_error is None:
                scored_response, extraction_error = extract_final_command(full_response)
            parsed = parse_model_response(scored_response)
            score = (
                base.score_response(trial_case, scored_response, rules)
                if provider_error is None and extraction_error is None
                else base.Score(False, False, False, None, False)
            )
            first_action = A_COMMAND[policy_id] if order == "a_first" else B_COMMAND[policy_id]
            second_action = B_COMMAND[policy_id] if order == "a_first" else A_COMMAND[policy_id]
            row = {
                "model": model,
                "repeat": repeat,
                "case_id": case.case_id,
                "policy_id": policy_id,
                "tier": case.tier,
                "language": language,
                "language_label": LANGUAGE_LABELS[language],
                "order": order,
                "interface": "deliberative_budget_1024",
                "instruction": instruction,
                "expected_command": parse_model_response(case.expected_command).normalized_cmd,
                "first_position_command": parse_model_response(first_action).normalized_cmd,
                "second_position_command": parse_model_response(second_action).normalized_cmd,
                "full_response": full_response,
                "response_chars": len(full_response),
                "scored_response": scored_response,
                "normalized_command": parsed.normalized_cmd,
                "valid": score.valid,
                "command_correct": score.command_correct,
                "action_family_correct": score.action_family_correct,
                "executable_correct": score.executable_correct,
                "selected_first_position": parsed.valid and parsed.normalized_cmd == parse_model_response(first_action).normalized_cmd,
                "selected_second_position": parsed.valid and parsed.normalized_cmd == parse_model_response(second_action).normalized_cmd,
                "final_extraction_error": extraction_error,
                "latency_ms": round(latency_ms, 3),
                "provider_error": provider_error,
                "ollama_done": response.get("done"),
                "ollama_done_reason": response.get("done_reason"),
                "ollama_eval_count": response.get("eval_count"),
                "ollama_prompt_eval_count": response.get("prompt_eval_count"),
                "ollama_eval_duration": response.get("eval_duration"),
                "ollama_prompt_eval_duration": response.get("prompt_eval_duration"),
                "ollama_total_duration": response.get("total_duration"),
            }
            rows.append(row)
            jsonl.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            jsonl.flush()
            marker = "ERR" if provider_error or extraction_error else ("OK" if score.command_correct else "MISS")
            print(
                f"[{index:>3}/{len(cells)}] {marker:4} {model} {language:15} {order:7} "
                f"{case.case_id} -> {parsed.normalized_cmd} expected={row['expected_command']} "
                f"reason={row['ollama_done_reason']} eval={row['ollama_eval_count']}"
            )

    write_csv(output / "results.csv", rows)
    summary = {
        "n_rows": len(rows),
        "provider_errors": sum(bool(r["provider_error"]) for r in rows),
        "final_extraction_errors": sum(bool(r["final_extraction_error"]) for r in rows),
        "done_reasons": sorted({str(r["ollama_done_reason"]) for r in rows}),
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"\nResults: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
