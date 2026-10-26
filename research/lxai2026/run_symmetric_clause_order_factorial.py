"""Run a clean post-freeze interface × clause-order factorial for LXAI 2026.

This full-paper control replaces the causal interpretation of the earlier
branch-reversal rewrite with a stricter manipulation.  For each of eight binary
policies, both prompt variants contain the SAME TWO EXPLICIT CLAUSES verbatim;
only the order of those clauses changes.  States and oracle commands are
unchanged.

Factors:
- interface: direct command vs explicit deliberation + FINAL line
- clause order: A-first vs B-first
- language: tuteo vs Rioplatense voseo
- model: supplied on CLI (intended: Mistral24 and Qwen30)

Default size with two models is 32 states × 2 languages × 2 orders ×
2 interfaces × 2 models = 512 calls.  This is a separate post-freeze control;
it never modifies the frozen 576-call dataset.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter
from typing import Any, Mapping, Sequence
from urllib.error import URLError
from urllib.request import urlopen

os.environ.setdefault("KIVY_NO_ARGS", "1")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import run_experiment as base  # noqa: E402
from direct_ollama_client import DirectOllamaChatClient  # noqa: E402
from game.replay_engine import parse_model_response  # noqa: E402
from game.research_runtime import extract_response_text  # noqa: E402
from run_decision_experiment import DECISION_SYSTEM_PROMPT  # noqa: E402
from run_deliberation_control import (  # noqa: E402
    SYSTEM_PROMPT as DELIBERATION_SYSTEM_PROMPT,
    extract_final_command,
)

LANGUAGES = ("es_standard", "es_rioplatense")
LANGUAGE_LABELS = {
    "es_standard": "Tuteo Spanish",
    "es_rioplatense": "Rioplatense voseo",
}
ORDERS = ("a_first", "b_first")
INTERFACES = ("direct", "deliberative")

# The clause strings are the experimental object.  For a given policy and
# language, A-first and B-first prompts contain these exact same strings and
# differ only in their order.  Optional `prefix` is identical in both orders.
CLAUSES: dict[str, dict[str, dict[str, str]]] = {
    "D1-P1": {
        "en": {
            "a": "When your shield is raised, lower it.",
            "b": "When your shield is down, fire.",
        },
        "es_standard": {
            "a": "Cuando tienes el escudo levantado, bájalo.",
            "b": "Cuando tienes el escudo bajo, dispara.",
        },
        "es_rioplatense": {
            "a": "Cuando tenés el escudo levantado, bajalo.",
            "b": "Cuando tenés el escudo bajo, dispará.",
        },
    },
    "D1-P2": {
        "en": {
            "a": "When your health is below 15, raise the shield.",
            "b": "When your health is 15 or higher, move forward.",
        },
        "es_standard": {
            "a": "Cuando tienes menos de 15 puntos de salud, levanta el escudo.",
            "b": "Cuando tienes 15 puntos de salud o más, avanza.",
        },
        "es_rioplatense": {
            "a": "Cuando tenés menos de 15 puntos de salud, levantá el escudo.",
            "b": "Cuando tenés 15 puntos de salud o más, avanzá.",
        },
    },
    "D2-P1": {
        "en": {
            "a": "When your health is lower than the opponent's health, raise the shield.",
            "b": "When your health is greater than or equal to the opponent's health, fire.",
        },
        "es_standard": {
            "a": "Cuando tienes menos salud que el rival, levanta el escudo.",
            "b": "Cuando tienes tanta o más salud que el rival, dispara.",
        },
        "es_rioplatense": {
            "a": "Cuando tenés menos salud que el rival, levantá el escudo.",
            "b": "Cuando tenés tanta o más salud que el rival, dispará.",
        },
    },
    "D2-P2": {
        "en": {
            "a": "When your x coordinate is greater than the opponent's x coordinate, turn counterclockwise 90 degrees.",
            "b": "When your x coordinate is less than or equal to the opponent's x coordinate, turn clockwise 90 degrees.",
        },
        "es_standard": {
            "a": "Cuando tu coordenada x es mayor que la del rival, gira 90 grados en sentido antihorario.",
            "b": "Cuando tu coordenada x es menor o igual que la del rival, gira 90 grados en sentido horario.",
        },
        "es_rioplatense": {
            "a": "Cuando tu coordenada x es mayor que la del rival, girá 90 grados en sentido antihorario.",
            "b": "Cuando tu coordenada x es menor o igual que la del rival, girá 90 grados en sentido horario.",
        },
    },
    "D3-P1": {
        "en": {
            "a": "When your health is below 15 and your shield is down, raise the shield.",
            "b": "When your health is 15 or higher or your shield is raised, fire.",
        },
        "es_standard": {
            "a": "Cuando tienes menos de 15 puntos de salud y el escudo está bajo, levanta el escudo.",
            "b": "Cuando tienes 15 puntos de salud o más o el escudo está levantado, dispara.",
        },
        "es_rioplatense": {
            "a": "Cuando tenés menos de 15 puntos de salud y el escudo está bajo, levantá el escudo.",
            "b": "Cuando tenés 15 puntos de salud o más o el escudo está levantado, dispará.",
        },
    },
    "D3-P2": {
        "en": {
            "a": "When exactly one of the two shields is raised, move forward.",
            "b": "When the two shields are in the same state, fire.",
        },
        "es_standard": {
            "a": "Cuando exactamente uno de los dos escudos está levantado, avanza.",
            "b": "Cuando los dos escudos están en el mismo estado, dispara.",
        },
        "es_rioplatense": {
            "a": "Cuando exactamente uno de los dos escudos está levantado, avanzá.",
            "b": "Cuando los dos escudos están en el mismo estado, dispará.",
        },
    },
    "D5-P1": {
        "en": {
            "a": "When your health is at least 10 points higher than the opponent's health, fire.",
            "b": "When your health is not at least 10 points higher than the opponent's health, raise the shield.",
        },
        "es_standard": {
            "a": "Cuando tienes al menos 10 puntos de salud más que el rival, dispara.",
            "b": "Cuando no tienes al menos 10 puntos de salud más que el rival, levanta el escudo.",
        },
        "es_rioplatense": {
            "a": "Cuando tenés al menos 10 puntos de salud más que el rival, dispará.",
            "b": "Cuando no tenés al menos 10 puntos de salud más que el rival, levantá el escudo.",
        },
    },
    "D5-P2": {
        "en": {
            "prefix": "First compute the horizontal distance between your x coordinate and the opponent's x coordinate.",
            "a": "When the distance is at least 0.4, move forward 0.1.",
            "b": "When the distance is below 0.4, turn clockwise 90 degrees.",
        },
        "es_standard": {
            "prefix": "Primero calcula la distancia horizontal entre tu coordenada x y la coordenada x del rival.",
            "a": "Cuando la distancia es de al menos 0.4, avanza 0.1.",
            "b": "Cuando la distancia es menor que 0.4, gira 90 grados en sentido horario.",
        },
        "es_rioplatense": {
            "prefix": "Primero calculá la distancia horizontal entre tu coordenada x y la coordenada x del rival.",
            "a": "Cuando la distancia es de al menos 0.4, avanzá 0.1.",
            "b": "Cuando la distancia es menor que 0.4, girá 90 grados en sentido horario.",
        },
    },
}

A_COMMAND = {
    "D1-P1": "S0",
    "D1-P2": "S1",
    "D2-P1": "S1",
    "D2-P2": "A90",
    "D3-P1": "S1",
    "D3-P2": "M",
    "D5-P1": "B",
    "D5-P2": "M0.1",
}
B_COMMAND = {
    "D1-P1": "B",
    "D1-P2": "M",
    "D2-P1": "B",
    "D2-P2": "C90",
    "D3-P1": "B",
    "D3-P2": "B",
    "D5-P1": "S1",
    "D5-P2": "C90",
}


def render_policy(policy_id: str, language: str, order: str) -> str:
    parts = CLAUSES[policy_id][language]
    ordered = [parts["a"], parts["b"]] if order == "a_first" else [parts["b"], parts["a"]]
    prefix = parts.get("prefix")
    return " ".join(([prefix] if prefix else []) + ordered)


def _command_output(args: Sequence[str]) -> str | None:
    try:
        completed = subprocess.run(
            list(args), cwd=ROOT, capture_output=True, text=True, check=False, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or completed.stderr.strip() or None


def _ollama_base_url(host: str, port: int) -> str:
    clean = str(host).rstrip("/")
    suffix = f":{int(port)}"
    return clean if clean.endswith(suffix) else clean + suffix


def _ollama_json(host: str, port: int, path: str) -> dict[str, Any] | None:
    try:
        with urlopen(_ollama_base_url(host, port) + path, timeout=5) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def collect_provenance(models: Sequence[str], host: str, port: int, suite_path: Path) -> dict[str, Any]:
    tags_payload = _ollama_json(host, port, "/api/tags") or {}
    available = tags_payload.get("models") if isinstance(tags_payload.get("models"), list) else []
    records: dict[str, Any] = {}
    for requested in models:
        matched = next(
            (
                item for item in available
                if isinstance(item, Mapping)
                and requested in {str(item.get("name") or ""), str(item.get("model") or "")}
            ),
            None,
        )
        records[requested] = dict(matched) if isinstance(matched, Mapping) else None
    return {
        "git_commit": _command_output(("git", "rev-parse", "HEAD")),
        "git_branch": _command_output(("git", "branch", "--show-current")),
        "python_version": sys.version,
        "ollama_version": (_ollama_json(host, port, "/api/version") or {}).get("version"),
        "models": records,
        "source_suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
        "clause_map_sha256": hashlib.sha256(
            json.dumps(CLAUSES, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "direct_prompt_sha256": hashlib.sha256(DECISION_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "deliberation_prompt_sha256": hashlib.sha256(DELIBERATION_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
    }


def selected_cases(suite_path: Path) -> tuple[dict[str, Any], list[base.TrialCase], dict[str, str]]:
    payload = json.loads(suite_path.read_text(encoding="utf-8"))
    original = {str(item["id"]): item for item in payload["cases"]}
    _, loaded = base.load_suite(suite_path)
    cases: list[base.TrialCase] = []
    policy_by_case: dict[str, str] = {}
    for case in loaded:
        policy_id = str(original[case.case_id]["policy_id"])
        if policy_id not in CLAUSES:
            continue
        policy_by_case[case.case_id] = policy_id
        cases.append(case)
    if len(cases) != 32:
        raise ValueError(f"Expected 32 selected cases, found {len(cases)}")
    return payload, cases, policy_by_case


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run symmetric clause-order LXAI factorial.")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--languages", nargs="+", choices=LANGUAGES, default=list(LANGUAGES))
    parser.add_argument("--orders", nargs="+", choices=ORDERS, default=list(ORDERS))
    parser.add_argument("--interfaces", nargs="+", choices=INTERFACES, default=list(INTERFACES))
    parser.add_argument("--suite", type=Path, default=HERE / "suite_decision_complexity.json")
    parser.add_argument("--host", default="http://localhost")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--order-seed", type=int, default=20260825)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    models = [m.strip() for m in args.models if m.strip()]
    suite_payload, cases, policy_by_case = selected_cases(args.suite)
    game_rules = base.rules()
    base.validate_suite(cases, game_rules)

    # Build complete cells, then shuffle deterministically by model.
    cells: list[tuple[str, int, base.TrialCase, str, str, str]] = []
    for model_index, model in enumerate(models):
        rng = random.Random(args.order_seed + model_index)
        groups = [
            (repeat, case, language, order, interface)
            for repeat in range(args.repeats)
            for case in cases
            for language in args.languages
            for order in args.orders
            for interface in args.interfaces
        ]
        rng.shuffle(groups)
        cells.extend((model, *group) for group in groups)
    if args.limit is not None:
        cells = cells[: max(0, args.limit)]

    planned = len(cells)
    print(f"Semantic states: {len(cases)} (8 binary policies × 4 states)")
    print(f"Models: {', '.join(models)}")
    print(f"Languages: {', '.join(args.languages)}")
    print(f"Orders: {', '.join(args.orders)}")
    print(f"Interfaces: {', '.join(args.interfaces)}")
    print(f"Planned model calls: {planned}")
    if args.dry_run:
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or HERE / "controls" / "symmetric_clause_factorial" / stamp
    output.mkdir(parents=True, exist_ok=True)

    metadata = {
        "experiment": "LXAI 2026 symmetric clause-order interface factorial",
        "relation_to_main_run": (
            "Separate post-freeze full-paper control. For each binary policy the two order variants "
            "contain the same explicit clauses verbatim and differ only in clause order."
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "languages": args.languages,
        "language_labels": LANGUAGE_LABELS,
        "orders": args.orders,
        "interfaces": args.interfaces,
        "n_semantic_states": len(cases),
        "n_invocations_planned": planned,
        "repeats": args.repeats,
        "temperature": args.temperature,
        "seed": args.seed,
        "order_seed": args.order_seed,
        "host": args.host,
        "port": args.port,
        "rules": game_rules.to_dict(),
        "source_suite": str(args.suite),
        "source_suite_version": suite_payload.get("version"),
        "clauses": CLAUSES,
        "a_commands": A_COMMAND,
        "b_commands": B_COMMAND,
        "direct_system_prompt": DECISION_SYSTEM_PROMPT,
        "deliberation_system_prompt": DELIBERATION_SYSTEM_PROMPT,
        "provenance": collect_provenance(models, args.host, args.port, args.suite),
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    client = DirectOllamaChatClient(host=args.host, port=args.port)
    rows: list[dict[str, Any]] = []
    with (output / "results.jsonl").open("w", encoding="utf-8") as jsonl:
        for index, (model, repeat, case, language, order, interface) in enumerate(cells, 1):
            policy_id = policy_by_case[case.case_id]
            instruction = render_policy(policy_id, language, order)
            trial_case = replace(case, variants={language: instruction})
            system_prompt = DECISION_SYSTEM_PROMPT if interface == "direct" else DELIBERATION_SYSTEM_PROMPT
            num_predict = 24 if interface == "direct" else 256
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": base.user_message(trial_case, language)},
            ]
            options = {
                "temperature": args.temperature,
                "seed": args.seed + repeat,
                "num_predict": num_predict,
            }
            started = perf_counter()
            try:
                response = client.chat(model=model, messages=messages, options=options, stream=False)
                full_response = extract_response_text(response)
                latency = (perf_counter() - started) * 1000.0
                provider_error = None
            except Exception as exc:
                full_response = ""
                latency = (perf_counter() - started) * 1000.0
                provider_error = f"{type(exc).__name__}: {exc}"

            extraction_error = None
            scored_response = full_response
            if provider_error is None and interface == "deliberative":
                scored_response, extraction_error = extract_final_command(full_response)
            parsed = parse_model_response(scored_response)
            score = (
                base.score_response(trial_case, scored_response, game_rules)
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
                "interface": interface,
                "instruction": instruction,
                "expected_command": parse_model_response(case.expected_command).normalized_cmd,
                "a_command": parse_model_response(A_COMMAND[policy_id]).normalized_cmd,
                "b_command": parse_model_response(B_COMMAND[policy_id]).normalized_cmd,
                "first_position_command": parse_model_response(first_action).normalized_cmd,
                "second_position_command": parse_model_response(second_action).normalized_cmd,
                "full_response": full_response,
                "scored_response": scored_response,
                "normalized_command": parsed.normalized_cmd,
                "valid": score.valid,
                "command_correct": score.command_correct,
                "action_family_correct": score.action_family_correct,
                "executable_correct": score.executable_correct,
                "selected_first_position": parsed.valid and parsed.normalized_cmd == parse_model_response(first_action).normalized_cmd,
                "selected_second_position": parsed.valid and parsed.normalized_cmd == parse_model_response(second_action).normalized_cmd,
                "final_extraction_error": extraction_error,
                "latency_ms": round(latency, 3),
                "provider_error": provider_error,
            }
            rows.append(row)
            jsonl.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            jsonl.flush()
            marker = "ERR" if provider_error or extraction_error else ("OK" if score.command_correct else "MISS")
            print(
                f"[{index:>4}/{planned}] {marker:4} {model} {language:15} {interface:12} {order:7} "
                f"{case.case_id} -> {parsed.normalized_cmd} (expected {row['expected_command']})"
            )

    write_csv(output / "results.csv", rows)
    summary = {
        "n_rows": len(rows),
        "provider_errors": sum(bool(r["provider_error"]) for r in rows),
        "final_extraction_errors": sum(bool(r["final_extraction_error"]) for r in rows),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"\nResults: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
