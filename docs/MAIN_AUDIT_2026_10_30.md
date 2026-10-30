> **[Project](../README.md) · [Documentation](README.md) · [Status](../STATUS.md) · [Release criteria](RELEASE_CRITERIA_1_0.md)**

# Merged-main audit — 30 October 2026

## Disposition

[PR #66](https://github.com/krahd/BatLLM/pull/66), the published Modelito 1.4.8 consumer migration, was merged into `main` as `b1f7d3dafe3f02ee87183edffb007415c65bc4cf`. The audit below concerns that exact application source. Version remains `0.3.6`.

The supported-Python source application passed the full automated suite and a complete native game/save/replay rehearsal. All five post-merge hosted workflows passed. Four findings remain open, including a bundle installation failure that the existing packaging smoke check misses. This establishes a tested development baseline, **not stable-release sign-off**. No runtime repairs or release publication form part of this audit.

## Open findings

### A1 — P1: bundle installation can succeed with an unsupported interpreter

The macOS installer calls bare `python3 -m venv` in [create_release_bundles.py](../create_release_bundles.py) (line 99). A supported Python 3.12 was installed on the audit machine, but its default `python3` was 3.15.2. Installing a fresh macOS bundle in a path containing spaces completed successfully and created a Python 3.15.2 environment. Both included launchers then exited with status 1:

```text
BatLLM requires Python 3.10 through 3.12. Detected Python 3.15.2.
BatLLM Game Analyzer requires Python 3.10 through 3.12. Detected Python 3.15.2.
```

The installer smoke check in [src/util/packaging_smoke.py](../src/util/packaging_smoke.py) (lines 181–196) checks the installer exit code and the existence of the environment's Python executable; it does not validate that interpreter or launch either application. Consequently, the combined install smoke passed on the same machine.

The Linux wrapper uses the same bare `python3` selection (line 136); Windows selects unqualified `py` or `python` (lines 57–58). Those are source-level risks, not native reproductions on those platforms.

**Required repair:** select or explicitly accept a supported interpreter, fail before installation if none is available, and make installer acceptance exercise compatibility and both launchers. The documented source setup with an explicitly selected Python 3.12 worked. The release bundle is not accepted for release by this audit.

### A2 — P2: native analyser file-row clicks do not update the selection

At 800×600 logical size, repeated single/double clicks on the main **Open Saved Session** file rows did not populate or change the selected-file preview. This reproduced in both the in-app and standalone analyser. Clicking a **Recent Sessions** button selected and opened the same file successfully. After selecting the valid save there, clicking `invalid_rules.json` in the main list left the valid save selected.

Evidence: [unchanged preview after clicking another file](audit-evidence/main-2026-10-30/file-selection-no-change.png). The relevant custom list layout is in [src/view/analyzer_load_screen.kv](../src/view/analyzer_load_screen.kv); the precise event-routing cause has not been isolated. The earlier scheduled refresh/selection tests do not establish physical pointer selection.

**Required repair:** restore native row selection and verify that the preview and opened file follow the clicked row. Recent Sessions is a tested workaround for files shown there.

### A3 — P2: gameplay controls clip and overlap at 800×600

The native game runs at this size, but command-history headings wrap one letter per line, column headings clip, and footer actions overlap or truncate. The maximised window allowed completion of the game and use of the footer controls.

Evidence: [800×600 gameplay capture](audit-evidence/main-2026-10-30/small-window.png). Relevant layout: [src/view/home_screen.kv](../src/view/home_screen.kv), especially the command column and footer. The screenshot is Retina-resolution and includes the macOS title bar.

**Required repair:** provide usable minimum-width behaviour or adapt the layout at small sizes, then repeat native pointer and readability checks. Enlarging the window is the tested workaround.

### A4 — P2: the model-download overall deadline is checked only between events

[src/llm/service.py](../src/llm/service.py) (lines 591–602) passes the full timeout to the Ollama client and checks elapsed time only after the streaming iterator returns an event. A read already in progress can exceed the remaining total budget.

A test-owned loopback HTTP server sent a progress record immediately and then every 0.5 seconds. With a preconstructed client to exclude client-initialisation overhead and a requested total timeout of 0.75 seconds, two events were yielded at 0.005 and 0.510 seconds; `TimeoutError` arrived at **1.015 seconds**, after the third record. No model was downloaded. See [measured result](audit-evidence/main-2026-10-30/download-deadline.json).

**Required repair:** apply one monotonic deadline to connection and streaming reads using the remaining budget, and cover a stall after a partial progress event. This finding concerns management downloads; it does not invalidate the separate strict Modelito inference deadline tests.

## Automated and hosted validation

Local validation used a fresh Python 3.12 environment with published `modelito==1.4.8`, with the package version and site-packages import path verified. The test suite ran on Python 3.12.15; Homebrew installation subsequently upgraded the host Python 3.12 to 3.12.16, which the native rehearsal used. Application and Kivy state were disposable and separate from normal user state. Research and packaging ran in a disposable archive of the merged source.

| Check | Result |
| --- | --- |
| `python run_tests.py full` | Core preflight: 4 passed; full suite: **310 passed, no skips**. The preflight is not an additional four unique tests. Real Ollama smoke was enabled. |
| Compilation of source, tools and entry points | Passed. |
| Maintained Pylint command | Passed, **8.83/10**; existing warnings remain. |
| `python tools/check_docs.py` | Passed before and after the audit documentation update. |
| `python -m pip check` | No broken requirements. |
| `python -m pip_audit -r requirements.txt` | No known vulnerabilities found in the resolved runtime requirements at audit time. |
| Full URUCON experiment pipeline | 60 valid sessions, 1,080 state/event-equivalent plays, 5,000 matching reference cases, 1,560/1,560 injected faults detected, 180/180 serialisation controls accepted. |
| Research artefact build | Passed; 206 files packaged. Generated results remained in the disposable copy. |
| Release archive and formula generation | Passed, including actual dependency resolution/hashes. |
| Combined installer and Homebrew install smoke | Returned success; its bundle-launch coverage gap is finding A1. Homebrew install/test/uninstall completed on Apple Silicon. |
| Actual macOS bundle launcher check | **Failed** for both launchers after a successful installer, as detailed in A1. |

The disposable research archive initially lacked Git metadata, so its generated corpus reported `source_revision: null`. It is validation output from the archived source, not a replacement for the committed reproducibility artefact or evidence of model execution.

All hosted workflows below completed successfully for `b1f7d3d`:

- [CI](https://github.com/krahd/BatLLM/actions/runs/41134545354): Python 3.10–3.12 across Linux, macOS and Windows, plus lint/documentation gates.
- [Multiplatform Validation](https://github.com/krahd/BatLLM/actions/runs/41134545337): platform bundles, Homebrew dry-run and mock-Ollama integration.
- [Python dependency audit](https://github.com/krahd/BatLLM/actions/runs/41134545310).
- [URUCON research validation](https://github.com/krahd/BatLLM/actions/runs/41134545396).
- [Pages build and deployment](https://github.com/krahd/BatLLM/actions/runs/41134543618).

Hosted bundle generation and mock smoke do not establish native installed-application acceptance.

## Native source and live-service validation

The native SDL2 rehearsal used installed Ollama `0.40.10` and `smollm2:latest`, with real model responses. The shipped game length was retained: **one complete game, two rounds, eight turns per round, 32 plays**. The disposable configuration used the explicit installed model tag and disabled automatic service control. Initial desktop attachment timeouts recovered after attaching to the current Python application path.

- Both players submitted round prompts; all 32 responses produced valid commands. The game completed by its round limit and presented Game Over. The model sometimes ignored the requested command; this is not evidence of prompt compliance or model quality.
- Native Save Session produced a schema-v2 file with one game, two rounds and sixteen turns.
- In-app and standalone Game Analyzer loaded the saved file; prompts/plays, step navigation and second-round navigation were exercised. The standalone process exited normally after closing its window.
- Legacy-list and invalid-rule files displayed explicit compatibility errors through the working Recent Sessions selection path.
- Independent verification traversed **all 48 replay positions with zero mismatches** and exercised all six text-formatting methods at each position. A tampered health value produced a mismatch, and both invalid controls were rejected.
- A separate test-owned Ollama server on an unused port started, warmed the existing model, created an ownership receipt, and stopped through the service API. The pre-existing external server remained running. No real model download, deletion or explicit unload was performed.

Selected evidence:

- [Game completion](audit-evidence/main-2026-10-30/game-complete.png).
- [In-app analyser](audit-evidence/main-2026-10-30/analyser-in-app.png) and [standalone analyser](audit-evidence/main-2026-10-30/standalone.png).
- [Invalid-rule rejection](audit-evidence/main-2026-10-30/invalid-rejected.png) and [legacy rejection](audit-evidence/main-2026-10-30/legacy-rejected.png).
- [Independent replay verification](audit-evidence/main-2026-10-30/native-verification.json) and [owned-service lifecycle result](audit-evidence/main-2026-10-30/lifecycle.json).

The authentic saved session remains local audit evidence rather than committed user state. Its SHA-256 is `0c0be15ed87be76b6049b0f6292f64a1e7ca6d295c4af68b5da0bb72fce9e766`. Analysis did not modify it.

## Limits and next acceptance work

The following gates remain unrun in this audit: native first-run on Linux and Windows; Homebrew GUI launch/game/save; missing-Ollama installation prompts; native stopped/unresponsive recovery paths; actual model downloads/deletion; native malformed-response handling, damage/fatal-shot completion and every save/exit/recovery combination; and accessibility acceptance. Historical checks in [the earlier native rehearsal](NATIVE_REHEARSAL_2026_10_27.md) are not claimed as new results here.

The Homebrew check installed and removed a temporary BatLLM formula/tap; no prior BatLLM formula was installed. Homebrew dependency changes, including the Python patch upgrade, remain. This was not a machine-wide rollback test.

Repair A1–A4, add focused coverage for the missed contracts, repeat their native/install acceptance, then complete the remaining [1.0 release gates](RELEASE_CRITERIA_1_0.md). Keep source stability, package installation, native usability and release sign-off as separate conclusions.
