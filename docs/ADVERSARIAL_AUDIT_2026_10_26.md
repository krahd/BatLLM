# Post-merge adversarial audit — 26 October 2026

## Baseline and result

PR [#62](https://github.com/krahd/BatLLM/pull/62) was merged into `main` as **`d86ae05d4c39689cf7134c556b0c8216a48e5336`**. Local main was fetched and fast-forwarded to that exact revision with a clean worktree before this audit. Version remains `0.3.6`.

This audit identifies **11 remaining findings: four high and seven medium priority**. Ten concern BatLLM behaviour or distribution; one is an upstream Modelito catalogue defect that BatLLM currently exposes without a useful recovery path. These are findings against the merged baseline, not a repair-completion record.

The previous repair materially improved the main gameplay/research inference boundary, service ownership, v2 action validation and test realism. Its broad service-safety claims did not cover the standalone configuration editor, and its packaging validation did not execute an extracted research package.

## Repair disposition

The repair accompanying PR [#63](https://github.com/krahd/BatLLM/pull/63) addresses R1–R10 in BatLLM and restores a usable, confirmed download workflow for R11. Modelito’s unsupported automatic catalogue discovery remains an upstream issue; BatLLM no longer runs its unsupported commands or presents their failure as an empty catalogue. The original baseline evidence is retained below.

| Finding | Implemented change and regression coverage |
| --- | --- |
| R1 | The standalone editor uses the shared strict chat transport and explicit-endpoint management facade, with real provider deadlines. Delete, named-model unload and downloads wait for confirmation. Console Stop retires only its own output and closes its stream iterator. Endpoint, deadline, confirmation, streaming and cancellation tests pass. |
| R2 | Initial and subsequent scheduled turns capture game/turn generations and active-round identity. Reset makes both callback kinds harmless; regression tests cover both windows. |
| R3 | The verifier uses the committed Draft 2020-12 JSON Schema before semantic checks. Malformed roots/containers return invalid reports; boolean actor/count/latency fields are rejected. The schema is included in platform bundles from its canonical source. |
| R4 | Research packages include the complete `src` tree, runtime resources, launchers and `VERSION`. An isolated extraction test generates a scripted trace and verifies it with the original checkout absent from the subprocess import path. |
| R5 | `Set Temporarily` stores an execution-only overlay. Incidental model/timeout saves write persistent preferences without flushing that overlay. Explicit defaults replace the relevant temporary values. |
| R6 | Effective context modes are loaded before headers and user content; changes reset histories. Generation options are frozen before message construction. Tests cover augmentation and independent-context changes, including cancellation after the mode changes. |
| R7 | Saved model names no longer imply ownership, and selection never automatically unloads other models. Explicit standalone unload requires confirmation. |
| R8 | Each selection has a generation token. Warm-up commits and failures return through the Kivy thread and ignore stale generations. A delayed older completion cannot replace the latest saved choice. |
| R9 | Service startup performs no pull. Missing-model warm-up reports a download-recovery instruction without recording model readiness or downloading anything. |
| R10 | Imported frozen rules use a strict required-field/type validator; application configuration retains its separate default/coercing constructor. Invalid or missing v2 rules are rejected instead of replaced silently. |
| R11 | Both interfaces accept an explicit model name and preserve download confirmation. Automatic discovery raises an actionable unavailable-catalogue message. The upstream Modelito defect is documented in the handoff. |

Repair validation on Python 3.12/macOS:

- Complete isolated non-live suite: **291 passed, 2 intentional live-test skips**.
- Full maintained Pylint gate: passed, **8.84/10**, no errors; existing warnings remain.
- Compilation, documentation validation, KV parsing and diff checks: passed.
- Homebrew formula generation with dependency resolution/hashes: passed, including the new `jsonschema` runtime dependency.
- Full research pipeline and package build in a temporary copy: passed; 60 valid traces/1,080 transitions, 5,000 reference cases, all 1,560 injected faults detected and all 180 serialisation controls accepted. Canonical research outputs and manuscript were preserved.
- Extracted research-package generation/verification is now a maintained regression test, rather than only an archive-construction check.

Console cancellation is cooperative: pending UI fragments are retired immediately; a blocked provider read remains bounded by the configured request deadline, and the iterator is closed when control returns. No service-wide stop is used. Real-model, native GUI and installed-package acceptance remain explicit release gates.

## High-priority findings

### R1 — Standalone configuration editor bypasses the repaired safety boundary

**Owner:** BatLLM integration, with Modelito dependencies.

`src/configs/configurator.py` retains its own `OllamaClient`, rather than using `llm.chat` and the repaired lifecycle facade:

- local inventory, model deletion and pull use Modelito helpers without the configured endpoint;
- whole-service Stop delegates to Modelito’s generic shutdown without BatLLM ownership checks;
- console Stop calls `_stop_models(None)`, which reaches whole-service shutdown;
- Delete starts a worker immediately without a confirmation gate; and
- synchronous and streaming inference put the configured timeout into `settings` instead of the provider constructor, so Modelito 1.4.6 uses its default deadline.

**Evidence:** [client and management methods](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/configs/configurator.py#L144-L198), [immediate deletion](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/configs/configurator.py#L444-L455), [console Stop](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/configs/configurator.py#L564-L569).

**Reproduced:** four isolated probes captured endpoint-free deletion, ownership-free service shutdown, omitted provider timeout, and immediate deletion without confirmation. All external operations were stubbed.

**Required repair:** route this maintained entry point through the same explicit-endpoint, strict-inference and owned-service operations as the main application. Confirm deletion and downloads; console cancellation should cancel its request rather than stop the entire server.

### R2 — Queued turn callbacks survive a game reset

**Owner:** BatLLM.

Inference-completion callbacks carry generation tokens, but the first-turn and next-turn `Clock.schedule_once(self.play_turn)` callbacks do not. `start_new_game()` retires the executor and changes the generation without cancelling or guarding those scheduled callbacks.

**Reproduced:** complete one turn, retain its scheduled next-turn callback, start a new game, then invoke the retained callback. It raises:

```text
ValueError: Cannot start a turn without an active round. Call start_round first.
```

**Evidence:** [round scheduling](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/game_board.py#L463-L466), [next-turn scheduling](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/game_board.py#L560-L565), [reset](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/game_board.py#L135-L158).

**Required repair:** retain/cancel scheduled turn events or wrap every scheduled turn with the generation and active-round identity. Test reset before the initial turn and between consecutive turns.

### R3 — The v3 verifier can crash on malformed input and accept schema-invalid types

**Owner:** BatLLM.

The Python structural validator iterates `round_entry.get('prompts', [])` without first validating the container. `prompts: null` and `prompts: 7` both raise `TypeError`, which `verify_payload()` does not convert into a failed verification report.

A separate type discrepancy comes from `isinstance(value, int)`: Python booleans pass integer-field checks. Replacing the first play’s actor with `true`, then recomputing the documented commitments, produced **`valid=True, schema_valid=True`**. The committed Draft 2020-12 JSON Schema rejected that same trace’s `bot_id`.

**Evidence:** [prompt-container iteration](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/session_v3.py#L216-L222), [integer-field checks](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/session_v3.py#L227-L254), [exception boundary](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/trace_verifier.py#L297-L306).

**Required repair:** validate every nested container before iteration, reject booleans in numeric identity/count fields, and align the Python validator with the committed schema. Add malformed-container and cross-validator type tests. This finding concerns structural/schema correctness; it does not establish model authentication.

### R4 — The research ZIP is not runnable independently of the checkout

**Owner:** BatLLM distribution.

The research package includes replay/verifier/runtime entry points but omits their transitive application imports, including `src/configs/app_config.py`. `replay_engine.py` imports `configs.app_config` immediately.

**Reproduced:** build the package from a temporary copy, extract it into a different directory, and execute its own `python run_batllm_verify.py --help` using the installed dependency environment. It fails before argument processing:

```text
ModuleNotFoundError: No module named 'configs'
```

**Evidence:** [package file selection](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/research/urucon2026/build_artifact.py#L18-L37), [replay import](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/replay_engine.py#L9).

**Required repair:** package the import/resource closure or ship an installable research runtime. Validate generation and verification from the extracted archive with the original checkout absent from `sys.path`. Building a ZIP successfully is insufficient for this gate.

## Medium-priority findings

| ID | Finding and reproduced evidence | Required repair |
| --- | --- | --- |
| R5 | **Temporary settings become saved defaults.** Save `total_rounds=2`, change it in memory to `9` as Set Temporarily does, then perform successful inference while `last_served_model` differs. The connector calls the whole-config `save()`, and the saved rounds value becomes `9`. [Temporary-setting path](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/view/settings_screen.py#L75-L79), [incidental save](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/ollama_connector.py#L466-L469). This violates the documented Set Temporarily contract. | Separate execution overrides from persisted preferences; narrowly persist last-served metadata without flushing temporary game/UI values. |
| R6 | **The first request after a UI context-mode change can use the old system header.** `process_settings()` constructs the header before `load_options()` imports the new UI configuration. A probe switched augmentation from true to false and captured an augmented header paired with plain user input. Configuration-driven context changes also bypass the explicit-argument mode-change reset. [Call order](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/ollama_connector.py#L397-L407), [configuration assignment](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/ollama_connector.py#L271-L276). | Resolve mode changes once before constructing headers, histories and user content; reset histories according to the effective mode transition. |
| R7 | **Persisted model names are treated as live ownership.** A new Ollama screen infers `_managed_model_name` from `last_served_model`. If another client now runs that model, selecting a different model unloads it automatically. The probe observed `stop('external-now')` based only on the saved name. [Initialisation](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/view/ollama_config_screen.py#L85-L86), [unload](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/view/ollama_config_screen.py#L852-L860). Server-process ownership checks do not cover this path. | Do not infer current model ownership from historical configuration. Require explicit confirmation before unloading models shared with other clients. |
| R8 | **An older asynchronous selection can overwrite a newer selection.** Queue Use Selected for A, then B; complete B’s worker before A’s. A becomes the saved model. The workers have no selection generation, cancellation or serialisation. [Selection worker](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/view/ollama_config_screen.py#L840-L884). | Serialise selections or use a generation/transaction guard covering warm-up, unloading, persistence and status updates. |
| R9 | **Service start always performs a model pull.** With a configured model, `start_service()` invokes `pull` even when the server is already running. Its startup confirmation describes starting/warming, while automatic startup can reach this path without a per-download confirmation. The stubbed probe captured `pull not-installed`; no real model was downloaded. [Unconditional pull](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/llm/service.py#L509-L523). | Start the daemon separately from model acquisition. Warm installed models; direct missing models through the explicit confirmed download flow. |
| R10 | **Malformed v2 gameplay values are silently replaced by defaults.** Setting saved `bullet_damage` to `"nonsense"` passes session validation; replay uses damage `5` and can report no mismatch. The retained settings still contain the invalid string. [Validator](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/session_schema.py#L77-L80), [coercing settings factory](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/game/replay_engine.py#L145-L157). | Use strict required-field/type validation for imported frozen rules. Keep default/coercing construction separate for application initialisation. |
| R11 | **Remote model discovery relies on unsupported Ollama CLI commands.** Modelito 1.4.6 tries `list/ls/models/llms --remote`, including `--json` variants. Installed Ollama client **0.40.10** exposes only `--help` for `list`; `ollama list --remote --json` returns `unknown flag: --remote`. Read-only Modelito enumeration returned `[]`. BatLLM’s bounded wrapper still presents this as an empty catalogue, leaving the selector-based download flow without choices. [BatLLM wrapper](https://github.com/krahd/BatLLM/blob/d86ae05d4c39689cf7134c556b0c8216a48e5336/src/llm/service.py#L558-L572). | **Upstream Modelito:** use a supported catalogue source or expose unsupported discovery explicitly. **BatLLM:** show a useful discovery error/recovery path, or allow explicit model-name entry with the existing download confirmation. |

## Modelito handoff

R11 is a newly reproduced upstream defect in the installed 1.4.6 package, specifically `modelito/ollama_service.py:list_remote_models()` around lines 761–769. Its current command list is:

```text
ollama list --remote --json
ollama ls --remote --json
ollama models --remote --json
ollama llms --remote --json
ollama list --remote
ollama ls --remote
ollama models --remote
ollama llms --remote
```

The official [Ollama CLI reference](https://docs.ollama.com/cli) documents local listing, pull and named-model stop; [the tags API](https://docs.ollama.com/api/tags) lists available local models. The installed client’s help and unknown-flag response supplied the direct compatibility evidence for this audit.

The previous [1.4.6 handoff](ADVERSARIAL_AUDIT_2026_10_25.md#modelito-handoff) remains applicable: lifecycle configuration, generic shutdown ownership, inconsistent subprocess-deadline parameters, ignored synchronous `settings['timeout']`, and completion-response validation. At the audited baseline, R1 demonstrated that BatLLM’s standalone editor reached several of those paths; the repair routes it through the guarded facade. No Modelito files were modified during this audit.

## Validation and limits

Fresh checks on the merged revision:

- Complete isolated Python 3.12/macOS non-live suite: **247 passed, 2 intentional live-test skips**.
- **15 isolated evidence probes passed**, meaning they reproduced the behaviours described above. They assert existing defects and were kept outside the maintained regression suite; this count is not a claim of 15 repaired cases.
- Read-only Ollama CLI help/version/unsupported-flag checks: client **0.40.10**; no running daemon was reachable. Modelito remote enumeration returned an empty list with an intentionally unreachable test endpoint.
- Documentation validation passed before report changes and again for this documentation update.
- The exact merged revision’s hosted **CI**, **Multiplatform Validation**, **Python dependency audit** and **URUCON research validation** completed successfully. Hosted CI includes Python 3.10–3.12 on Linux, macOS and Windows. These green checks do not cover the new findings.
- Research ZIP construction/extraction used temporary copies; committed research corpus, results and artefacts were preserved.

Scope included gameplay scheduling, connector state, configuration/persistence, both management interfaces, v2/v3 validation, replay, research packaging, release packaging and workflow configuration. Reproductions used a temporary `BATLLM_HOME`, mock Kivy objects and stubbed service/destructive actions. No real model generation, server start/stop, model pull/delete, native GUI acceptance or installed-package testing was performed.

## Recommended repair order

1. Close R1 and R2: unify the remaining management surface and guard all scheduled game work.
2. Close R3 and R4: align schema validation and validate the extracted research distribution.
3. Repair persistence and context changes (R5–R6), then selection ownership/concurrency (R7–R8).
4. Separate daemon startup from downloads (R9), enforce imported rule types (R10), and coordinate the Modelito catalogue repair/recovery path (R11).

The audit did not establish a new critical silent-inference-fallback defect in the repaired strict adapter. The baseline findings prevented stable-release sign-off. The repair disposition above records their current handling; native and real-model acceptance gates remain open.
