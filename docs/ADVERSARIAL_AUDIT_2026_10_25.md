# Adversarial audit verification — 25 October 2026

The supplied audit targets `d2280b9`, which matched the clean checkout at the start of this repair. The principal findings are supported by that source. BatLLM pinned Modelito 1.4.5 even though 1.4.6 already repaired native strict inference. This verification inspected the installed 1.4.6 package and exercised the application against isolated HTTP servers; it did not operate a real Ollama service.

## Findings and disposition

| Finding | Verification and repair |
| --- | --- |
| C1, H1, H5, H7 | Confirmed for the pinned 1.4.5 adapter. Updated both dependency pins to 1.4.6. Desktop and research share `src/llm/chat.py`, explicitly request strict inference, pass native options and structured messages, and set the provider timeout. No CLI or deterministic inference fallback is enabled. HTTP tests capture the actual request body and exercise failure responses. |
| C2 | Confirmed. Removed Modelito configuration discovery and top-level lifecycle delegation. Inspection, start, management operations and stop use BatLLM’s resolved endpoint and preferences. Local inventory uses explicit-endpoint HTTP; pull and deletion use an explicitly configured SDK client. Remote catalogue parsing is isolated in a bounded subprocess without local inventory discovery. |
| H2 | Confirmed. Snapshot conversation histories before each round and restore them on cancellation, replacing active lists and retiring callbacks. Regression coverage verifies that cancelled replies do not remain in context. |
| H3 | Confirmed. Validate every v2 play’s mapping, actor identity, response and command types; validate prompt records before the analyser consumes them. Malformed records raise `SessionFormatError`. |
| H4, M7 | Confirmed limitations. Preserve v2’s recorded-command replay for diagnostic compatibility, but report response–command disagreement, initial-state discontinuity and discontinuity between adjacent turns as replay mismatches. Matching saved states alone no longer yields an unqualified replay match. |
| H6 | Confirmed. Shutdown no longer discovers arbitrary listeners or unloads every running model. It requires a BatLLM ownership receipt, exact process creation time, Ollama identity and `serve` command. Reused PIDs and external listeners are not terminated. |
| M1 | Confirmed. Save selection only after the candidate model is ready; readiness failure preserves the previous saved selection. Warm the candidate before stopping a previously managed model. |
| M2 | Confirmed. UI timeout inputs and timeout resolution require finite positive values. The shared transport rejects invalid deadlines. |
| M3 | Confirmed. Reject non-mapping YAML documents and sections before merging, with an explanatory `ValueError`. Both application and service configuration use this loader. This is structural validation, not a complete typed schema for every game setting. |
| M4 | Confirmed. Local CLI calls have 30-second deadlines (600 seconds for pull); the GUI helper has a 900-second deadline; remote catalogue discovery has a 30-second deadline. Worker errors become visible status/log messages. SDK management requests are bounded, with an overall progress-loop download deadline. |
| M5 | Confirmed. Startup inspection runs in a worker and returns through Kivy’s clock. Session saving captures local configuration metadata and performs no live model-metadata lookup. |
| M6 | Confirmed. Default relative session folders now share the user data directory with preferences. Legacy JSON files are copied without overwriting user files or deleting originals. Explicit `BATLLM_HOME` and absolute paths retain their meaning. |
| M8 | Confirmed. Escape retained prompt, response, command, model and metadata values before applying deliberate analyser markup; escape preview filenames and textual metadata. Existing history formatters already escaped raw conversation content. |
| M9 | Confirmed. The old positional `None` bound to Modelito’s `host`. Removed this delegation entirely; no incompatible stop call remains. |
| L1 | Confirmed. Rendering no longer writes coordinates. Initial positions are generated within bot bounds; round-rule transitions normalise positions before recording the round snapshot. |
| L2 | Confirmed. Platform bundles now include runtime files and launchers, excluding tests, development documentation, screenshots and research archives. Full source archives remain separate. Research packaging includes the new shared transport. |

The CI mock now returns NDJSON when `stream` is omitted, reflecting Ollama’s default. The smoke check requires the requested `OK` response rather than any non-empty text. Native wire tests run as part of the ordinary non-live suite. All workflow action references are immutable commits; the dependency-review tag was corrected to the published `v5.0.0` commit because a bare `v5` reference was absent during verification.

Installation now opens the official Ollama download page after the existing confirmation flow. BatLLM does not execute downloaded shell/PowerShell installer content. Platform-specific command-description helpers remain available for compatibility, but the application installation path does not execute them.

## Modelito handoff

The following are upstream findings in the installed **1.4.6** source, separate from BatLLM’s repaired integration. No Modelito repository files were changed.

1. `modelito/ollama_service.py`: default lifecycle configuration still searches independently; local inventory, remote catalogue installed-state discovery, pull and deletion lack an explicit endpoint parameter. Expose an effective configuration/endpoint argument consistently, without silently discovering different user configuration. BatLLM now supplies its own lifecycle orchestration and explicit SDK client.
2. `stop_service(host, port, verbose, config_path)`: generic shutdown still unloads all running models and discovers/kills listeners without tracking ownership. Add process identity/ownership checks and preserve externally started servers. The previous BatLLM call `stop_service(None, verbose=...)` was a BatLLM call-site bug, not a valid Modelito API invocation.
3. `run_ollama_command()` and CLI-based management helpers do not consistently expose subprocess deadlines. Add timeout parameters and propagate timeout/cancellation failures. BatLLM runs its own bounded CLI calls and isolates remote catalogue discovery.
4. `OllamaProvider._strict_summarize()` uses `self.timeout`, while a caller-supplied `settings['timeout']` is ignored. Document one timeout authority or honour that setting consistently. BatLLM explicitly resolves it into the provider constructor, verified using a delayed HTTP server.
5. `_strict_summarize()` validates textual content but does not require `done: true` or validate response model identity. An incomplete single JSON message can therefore be accepted as a completion. Consider rejecting explicitly incomplete responses and validating response identity under a documented alias policy. BatLLM’s current contract tests cover invalid/empty bodies and unexpected NDJSON, but do not authenticate model identity or serving binaries.

Modelito 1.4.6 **does fix** the audit’s primary 1.4.5 defects when used with `strict=True`: no silent inference fallback, native message roles, generation-option transmission, and non-streaming requests. The request-deadline setting must be passed as described above.

## Validation and limits

Executed locally on Python 3.12/macOS:

- Complete isolated non-live suite: **247 passed, 2 skipped**. The skips are the intentionally gated live Ollama smoke checks.
- Full maintained Pylint command: passed, **8.89/10**, no errors; existing warnings remain.
- Python compilation and `git diff --check`: passed.

- Documentation validation: passed.
- Platform/source release generation and archive-member smoke validation: passed; runtime bundles exclude research and development files.
- Homebrew formula generation with actual dependency downloads and hashes: passed; no Homebrew installation.
- Complete research experiment pipeline and package build in a temporary copy: passed. All 60 traces and 1,080 transitions verified; 5,000 reference cases matched; all 1,560 injected faults were detected; all 180 benign serialisation variants were accepted. Tracked corpus/results and canonical manuscript were preserved.
- `pip check`: passed.

Local sandbox restrictions required elevated execution for loopback socket tests and networked dependency resolution. The initial native-window attempt aborted in SDL; subsequent automated checks used the repository’s documented mock-window environment. This provides no native GUI acceptance evidence.

No real model inference, service shutdown, model download/deletion, native GUI first-run acceptance, installed release-bundle acceptance or Homebrew installation was performed. These remain explicit 1.0 release gates. Passing synthetic HTTP tests cannot retroactively establish that old live traces were generated by the intended model, or that an Ollama server honoured every requested option.
