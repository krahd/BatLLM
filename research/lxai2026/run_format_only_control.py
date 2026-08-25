"""Run a post-freeze format-only control on the clean symmetric clause-order suite.

The model must emit exactly `FINAL: <command>` and is explicitly forbidden to
emit intermediate reasoning.  This isolates the final-output convention from
the explicit-deliberation permission while preserving the same 32 states,
languages, clause orders, models, seed, transport, parser and scoring.
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
from run_deliberation_control import extract_final_command
from run_symmetric_clause_order_factorial import (
    A_COMMAND, B_COMMAND, LANGUAGE_LABELS, LANGUAGES, ORDERS,
    collect_provenance, render_policy, selected_cases,
)

HERE = Path(__file__).resolve().parent

FORMAT_ONLY_PROMPT = """You control bot 1 in BatLLM.
In [GAME_STATE], bot 1 is you and bot 2 is the opponent.
[PLAYER_INPUT] gives a policy for choosing the current action.
Apply that policy to the current GAME_STATE before selecting a command. Use the
actual state values and evaluate comparisons, Boolean conditions, arithmetic,
and branches exactly as written.

Do not output reasoning, explanation, scratchpad, JSON, Markdown, or code fences.
Return exactly one line in this form and nothing else:
FINAL: <command>

where <command> is exactly one valid BatLLM command token:
B = fire
S1 = set shield on
S0 = set shield off
S = toggle shield
M = move forward by the default step
M<number> = move forward by that normalised distance
C<number> = rotate clockwise by that many degrees
A<number> = rotate counterclockwise by that many degrees

The JSON state fields are health, x, y, rot (degrees), and shield. true means
the shield is on and false means it is off."""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--languages", nargs="+", choices=LANGUAGES, default=list(LANGUAGES))
    p.add_argument("--orders", nargs="+", choices=ORDERS, default=list(ORDERS))
    p.add_argument("--suite", type=Path, default=HERE / "suite_decision_complexity.json")
    p.add_argument("--host", default="http://localhost"); p.add_argument("--port", type=int, default=11434)
    p.add_argument("--temperature", type=float, default=0.0); p.add_argument("--seed", type=int, default=20260825)
    p.add_argument("--order-seed", type=int, default=20260825); p.add_argument("--num-predict", type=int, default=256)
    p.add_argument("--repeats", type=int, default=1); p.add_argument("--output-dir", type=Path); p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    models=[m.strip() for m in args.models if m.strip()]
    suite_payload,cases,policy_by_case=selected_cases(args.suite)
    rules=base.rules(); base.validate_suite(cases,rules)
    cells=[]
    for mi,model in enumerate(models):
        rng=random.Random(args.order_seed+mi)
        groups=[(rep,case,lang,order) for rep in range(args.repeats) for case in cases for lang in args.languages for order in args.orders]
        rng.shuffle(groups); cells.extend((model,*g) for g in groups)
    print(f"Planned model calls: {len(cells)}")
    if args.dry_run: return 0

    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output=args.output_dir or HERE/"controls"/"format_only"/stamp; output.mkdir(parents=True,exist_ok=True)
    metadata={
        "experiment":"LXAI 2026 format-only post-freeze control",
        "models":models,"languages":args.languages,"orders":args.orders,"n_semantic_states":len(cases),
        "n_invocations_planned":len(cells),"repeats":args.repeats,"temperature":args.temperature,"seed":args.seed,
        "order_seed":args.order_seed,"num_predict":args.num_predict,"system_prompt":FORMAT_ONLY_PROMPT,
        "source_suite_version":suite_payload.get("version"),"provenance":collect_provenance(models,args.host,args.port,args.suite),
    }
    (output/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    client=DirectOllamaChatClient(host=args.host,port=args.port); rows=[]
    with (output/"results.jsonl").open("w",encoding="utf-8") as jsonl:
        for i,(model,rep,case,lang,order) in enumerate(cells,1):
            pid=policy_by_case[case.case_id]; instruction=render_policy(pid,lang,order); trial=replace(case,variants={lang:instruction})
            messages=[{"role":"system","content":FORMAT_ONLY_PROMPT},{"role":"user","content":base.user_message(trial,lang)}]
            started=perf_counter()
            try:
                response=client.chat(model=model,messages=messages,options={"temperature":args.temperature,"seed":args.seed+rep,"num_predict":args.num_predict},stream=False)
                full=extract_response_text(response); latency=(perf_counter()-started)*1000; provider_error=None
            except Exception as exc:
                response={}; full=""; latency=(perf_counter()-started)*1000; provider_error=f"{type(exc).__name__}: {exc}"
            scored, extraction_error=("",None)
            if provider_error is None: scored,extraction_error=extract_final_command(full)
            parsed=parse_model_response(scored)
            score=base.score_response(trial,scored,rules) if provider_error is None and extraction_error is None else base.Score(False,False,False,None,False)
            first=A_COMMAND[pid] if order=="a_first" else B_COMMAND[pid]; second=B_COMMAND[pid] if order=="a_first" else A_COMMAND[pid]
            row={
                "model":model,"repeat":rep,"case_id":case.case_id,"policy_id":pid,"tier":case.tier,"language":lang,
                "language_label":LANGUAGE_LABELS[lang],"order":order,"interface":"format_only","instruction":instruction,
                "expected_command":parse_model_response(case.expected_command).normalized_cmd,"first_position_command":parse_model_response(first).normalized_cmd,
                "second_position_command":parse_model_response(second).normalized_cmd,"full_response":full,"response_chars":len(full),"scored_response":scored,
                "normalized_command":parsed.normalized_cmd,"valid":score.valid,"command_correct":score.command_correct,
                "selected_first_position":parsed.valid and parsed.normalized_cmd==parse_model_response(first).normalized_cmd,
                "selected_second_position":parsed.valid and parsed.normalized_cmd==parse_model_response(second).normalized_cmd,
                "final_extraction_error":extraction_error,"latency_ms":round(latency,3),"provider_error":provider_error,
                "ollama_done_reason":response.get("done_reason"),"ollama_eval_count":response.get("eval_count"),
            }
            rows.append(row); jsonl.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n"); jsonl.flush()
            mark="ERR" if provider_error or extraction_error else ("OK" if score.command_correct else "MISS")
            print(f"[{i:>3}/{len(cells)}] {mark:4} {model} {lang:15} {order:7} {case.case_id} -> {parsed.normalized_cmd}")
    write_csv(output/"results.csv",rows)
    (output/"summary.json").write_text(json.dumps({"n_rows":len(rows),"provider_errors":sum(bool(r['provider_error']) for r in rows),"final_extraction_errors":sum(bool(r['final_extraction_error']) for r in rows)},indent=2)+"\n")
    print(f"Results: {output}"); return 0

if __name__=="__main__": raise SystemExit(main())
