# Native gameplay, saving and analyser audit — 27 October 2026

The macOS source workflow completed with real Ollama inference: two complete games, native session saving, in-app analysis, standalone analysis and save-on-exit. The exported session replays without a mismatch. Three usability defects were confirmed and repaired in the follow-up recorded below. This is bounded functional acceptance of this source checkout, not 1.0 or multiplatform release sign-off.

## Tested environment and scope

- Application: `0.3.6`, source commit `3bd5e5ce4d666fc9dde5b4eddf11caf448a50904`, based on `audit/post-merge-20261026`.
- Apple Silicon macOS `26.7.1`, Apple M1 Max; Python `3.12.15`, Kivy `2.3.1`, KivyMD `1.2.0`, Modelito `1.4.6`.
- Ollama `0.40.10`, existing server at `http://localhost:11434`; installed `smollm2:latest` (`1.7B`, `Q8_0`). No inference responses were stubbed in the native rehearsal.
- Source launchers: `run_batllm.py` and `run_game_analyzer.py`. Both `BATLLM_HOME` and `KIVY_HOME` pointed to disposable directories outside the checkout. Model selection and preference writes affected that isolated profile.
- Native windows were inspected through screenshots and operated with actual mouse/keyboard input. Two initial computer-control attachment calls timed out; the launcher was retried and native control subsequently recovered. Those failed attachment attempts provide no gameplay acceptance evidence and do not establish an application hang.
- Gameplay used **Set Temporarily**: two rounds and two turns per round. These are complete configured games, rather than completion of the shipped eight-turn-per-round profile.

## Executed native rehearsal

| Check | Result and evidence |
| --- | --- |
| Start source application | Native SDL2/OpenGL window rendered bots and controls. Settings and Ollama Config responded. |
| Refresh/select local model | Local Models listed 18 installed models. Selected `smollm2:latest`, pressed **Use Selected**, observed successful readiness and the selected/last-served values in the isolated preferences. |
| Independent contexts, augmentation enabled | Game 1 completed two rounds. Round 1 requested `C90` and `M0.03`; round 2 requested `S0` and `B`. All eight responses were valid commands. Rotation, movement and shields changed visibly; firing did not damage either bot in this random layout. |
| Round/game lifecycle | Round completion, Game Over and automatic fresh-game creation were visible. Both completed games ended through the round limit with both bots at 30 health. The empty automatically created third game was omitted from the export. |
| Shared context, augmentation disabled | Game 2 completed two rounds after changing both checkboxes temporarily. Round 1 requested `BANANA` and `A45`; round 2 requested `S1` and `C45`. Shared context is intentionally not private to either bot. |
| Invalid real-model responses | Two `BANANA` responses and one prose response became red `ERR` commands. The round and subsequent round completed. The analyser retained the raw responses, showed error badges and filtered the erroneous turns. |
| History | Bot-specific prompts, raw responses, normalised commands and state changes were readable after the first round. The session overview retained both games. |
| Native Save Session | Confirmation and filename dialogs produced `native-rehearsal.json`, then `native-rehearsal-multigame.json`, in the isolated saved-session directory. No `.batllm-*.tmp` files remained. |
| Temporary/default separation | Saved round rules contained two turns, while the profile's persistent defaults retained eight. Persistent context/augmentation defaults remained enabled after the temporary disabled condition. Shipped defaults retained their original checksum. |
| In-app analyser | Loaded through Recent Sessions; navigated games/rounds and an individual action; inspected Prompts, Plays, State Diff, Model, Round Settings and Insights. Automatic playback reached the last action and stopped. |
| Diagnostic controls | Error and Mismatch filters worked. A separately labelled copy with one altered post-state coordinate displayed a replay mismatch and a subsequent continuity warning. The authentic save had neither. |
| Compatibility rejection | Native **Open Analyzer** remained on the load screen for a legacy `[]` export and a copy containing string-valued `bullet_damage`; both showed explicit compatibility errors. |
| Standalone analyser | Launched with the exact gameplay export as a command-line argument. Navigated Game 2, stepped an action, inspected raw erroneous output, reloaded, returned to the picker and reopened the export through the file list. |
| Back, Esc and exit | In-app analyser Back/Esc returned through selection to Home. Home Esc displayed confirmation; **No** cancelled exit. Enabling save-on-exit temporarily, confirming exit and saving `native-save-on-exit.json` closed gameplay with exit code 0. Standalone Esc returned to selection and then closed with exit code 0. |
| Shared service after exit | `/api/version` still returned `0.40.10`. No server start/stop, download, deletion or explicit model unload was performed. |

The two games produced 16 real responses: 13 valid commands and 3 malformed responses. The valid commands comprised movement, clockwise and anticlockwise rotation, explicit shield changes and firing. This demonstrates handling of those commands; native damage, shield-block geometry and fatal-shot completion were not established by these layouts.

## Independent saved-file verification

The production `load_session_payload()` and `AnalyzerSessionModel` loaded the file outside the running GUI. Verification traversed every game, round, turn start and individual play, checked replay/continuity warnings and exercised all six text-formatting methods at every step.

| Measurement | Result |
| --- | --- |
| Exported games / rounds / completed turns / plays | `2 / 4 / 8 / 16` |
| Replay positions traversed | `24` |
| Replay or continuity mismatches in authentic save | `0` |
| Malformed real responses preserved as `ERR` | `3` |
| Deliberately altered state detected | Yes |
| Legacy and malformed-rule copies rejected | Yes |
| Authentic save checksum before/after analyser use | Unchanged |

SHA-256 of `native-rehearsal-multigame.json`:

```text
9979b9929e3ab867a8b1743b72737db0bb50d9d160161c7e79c8306288ab53a1
```

The original exports and full-resolution captures remain in the disposable rehearsal directory supplied with the audit handoff; they are not committed as application state. The [verification summary](audit-evidence/native-2026-10-27/verification.json) preserves the counts, commands, raw malformed outputs and rejection messages. Selected screenshots are retained below. The altered/invalid copies are controls, not gameplay results.

## Confirmed findings from the original rehearsal

### N1 — P2: compatible-file preview overlaps its heading

Select either valid native export in the load screen. The eight-line summary collides with **Selected File** and reaches the lower boundary of the panel. This occurred in both in-app and standalone views at the tested maximised size. The short rejection summaries do not have this collision.

The fixed-height panel and unconstrained summary label in [analyzer_load_screen.kv](../src/view/analyzer_load_screen.kv) do not reserve sufficient space for the summary's text. Loading still works. Give the summary adequate measured height or a scrollable area, then inspect the valid-file case at multiple window sizes.

### N2 — P2: Refresh leaves the main file list stale

After a new session/file appears in the current directory, press **Refresh**. Recent Sessions updates, but the main file list retains its previous entries. This was observed after the second native save, and reproduced in the standalone analyser by adding `refresh-probe.json`: it appeared on the left but not on the right after Refresh.

The button calls only `refresh_recent_sessions()` in [analyzer_load_screen.kv](../src/view/analyzer_load_screen.kv); that method does not refresh the file chooser in [analyzer_load_screen.py](../src/view/analyzer_load_screen.py). Recent Sessions provides a working route to the new save. Refresh both representations and preserve selection sensibly.

### N3 — P3: untagged model alias gets a false stopped label

With the shipped configured name `smollm2`, Ollama Config showed `Running models: smollm2:latest` and simultaneously described BatLLM's `smollm2` as “configured, not currently running”. Selecting the canonical tagged name corrected the label and gameplay worked.

`_format_status_report()` uses exact string membership in [ollama_config_screen.py](../src/view/ollama_config_screen.py). Resolve an omitted tag to `latest` when comparing identities, without conflating distinct explicit tags. This is a status-reporting defect, not evidence that inference failed.

### V2 provenance limitation

These saves support deterministic board replay, but do not record `independent_contexts` or `prompt_augmentation` per round. The metadata builder records configured/last-served model settings at save time, rather than an invocation ledger. The two experimental conditions above therefore rely on this observed rehearsal record; the exported v2 file alone cannot recover them or prove model/history identity per request. Do not treat the v2 export as a substitute for a research trace. No claim of cryptographic execution or weight authentication is made.

## Automated validation run in this audit

| Check | Actual result |
| --- | --- |
| Gameplay, analyser and compact-history regression files | `48 passed` |
| `python run_tests.py non-live` | Core phase `4 passed`; complete phase `291 passed, 2 skipped` |
| Entire `src/tests` suite with `BATLLM_RUN_OLLAMA_SMOKE=1` and isolated `BATLLM_CONFIG_PATH` | `293 passed`, no skips |
| `python tools/check_docs.py` and `git diff --check` | Passed |

All automated test runs used mock-window Kivy; these results complement the separate native UI rehearsal. The live-enabled suite exercised the existing server without the `run_tests.py full` wrapper's start/stop operations. No install-level packaging operation was run. The complete test invocations were:

```bash
KIVY_WINDOW=mock KIVY_NO_ARGS=1 KIVY_NO_CONSOLELOG=1 \
  python run_tests.py non-live
BATLLM_RUN_OLLAMA_SMOKE=1 BATLLM_CONFIG_PATH="$REHEARSAL_HOME/config.yaml" \
  KIVY_WINDOW=mock KIVY_NO_ARGS=1 KIVY_NO_CONSOLELOG=1 \
  python -m pytest -q src/tests
```

`REHEARSAL_HOME` denotes the disposable BatLLM profile. The pytest configuration supplies an additional isolated `BATLLM_HOME` for test configuration writes; the smoke tests read the explicit rehearsal configuration path. Save-on-exit was also validated independently: its exported `games` value exactly matched the earlier two-game export.

## Evidence and remaining gates

- [Native game completion](audit-evidence/native-2026-10-27/game-completion.jpg).
- [Analyser plays, state differences, metadata and frozen rules](audit-evidence/native-2026-10-27/analyser-tabs.jpg).
- [Real-model malformed output and error filtering](audit-evidence/native-2026-10-27/real-model-errors.jpg).
- [Native compatibility errors](audit-evidence/native-2026-10-27/compatibility-errors.jpg).
- [Deliberate mismatch detection](audit-evidence/native-2026-10-27/mismatch-detection.jpg).
- [Standalone launch with the gameplay save](audit-evidence/native-2026-10-27/standalone.jpg).
- [Stale refresh and overlapping preview](audit-evidence/native-2026-10-27/refresh-and-preview.jpg).
- [Model-alias status inconsistency](audit-evidence/native-2026-10-27/model-alias-status.jpg).

The requested source gameplay/save/analyser path now has native macOS evidence. The original rehearsal audited N1–N3; the follow-up below records their repair and separate validation. Native missing/stopped/unresponsive-Ollama flows, in-flight cancellation/saving, filesystem-failure recovery, fatal damage and all exit-setting combinations were not exhaustively rehearsed; relevant automated coverage is not a native substitute. Clean installation, install-level Homebrew/bundle checks, native Linux/Windows checks and the remaining 1.0 UI/accessibility work remain unsigned. Neither this audit nor passing tests authorises a release.

## Verification and repair — 27 October 2026

Rechecked the report against PR #65, its screenshots, the original exported file and the current source. N1–N3 are confirmed. The original save still has the SHA-256 above, and a fresh traversal through the production loader and analyser found zero mismatches across all 24 positions. The six analyser text-formatting methods also succeeded at every position. This corroborates the retained evidence; it is not a fresh real-model gameplay rehearsal.

| Finding | Repair and evidence |
| --- | --- |
| N1 | The preview uses a measured text height inside a vertical scroll area, with a bounded panel height. Native SDL2 rendering at 1440×900, 1024×768 and 800×600 logical window sizes showed a clear heading and contained text; a long filename remains readable by scrolling. The resize check exposed the same overflow in the Recent Sessions footer, which now uses the same containment. |
| N2 | Refresh rescans the currently browsed directory as well as Recent Sessions, retains an existing selection, revalidates its preview and clears a deleted selection. Regression tests exercise Kivy's actual directory scan in both the default save folder and another folder. A native check dispatched the Refresh button and verified file addition/removal and retained selection. |
| N3 | Status comparison resolves an omitted tag to `latest`, including namespaced names and registry ports. Eleven cases cover aliases, explicit tags, different namespaces and no loaded model. The displayed/configured names and model-management operations are unchanged. |

The Refresh and alias regressions produced six expected failures against the original code, then passed after repair. The complete non-live suite passed **304 tests, with 2 intentional live-test skips** (plus the runner's 4-test core phase). The focused analyser/Ollama screen suite passed **67 tests**. The maintained Pylint gate passed at **8.84/10**; documentation, KV parsing and diff checks passed. An initial sandboxed full-suite attempt could not bind its temporary HTTP servers; the successful rerun permitted loopback binding. The native render check likewise required desktop access.

The native follow-up used the production standalone analyser screens with scheduled UI events, disposable `BATLLM_HOME`/`KIVY_HOME` directories and copies of the original export. It did not repeat the earlier mouse/keyboard gameplay rehearsal. Retained follow-up evidence:

- [Native layout and refresh measurements](audit-evidence/native-2026-10-27/repair-verification.json).
- [Preview at 1024×768](audit-evidence/native-2026-10-27/repaired-preview-1024x768.png).
- [Long filename at 800×600, scrolled to the final summary lines](audit-evidence/native-2026-10-27/repaired-preview-800x600-bottom.png).

These are UI repairs for RC hardening. Game rules, prompting/context modes, inference, session formats, defaults and version `0.3.6` are unchanged. The v2 provenance limitation remains unchanged and explicit. PR #65 remains stacked on unmerged PR #63; the protected-main workflow matrix has not run on this repair commit because the stacked PR targets the repair branch. Install-level Homebrew/bundle checks, native Linux/Windows acceptance and the other release gates above remain unsigned. No release tag or RC sign-off is implied.
