# Workshop stabilisation — 27 October 2026

## Checkpoint and scope

Initial worktree: clean `audit/post-merge-20261026`, synchronised with origin.
Canonical remote: `git@github.com:krahd/BatLLM.git`.
Fetched main: `d86ae05d4c39689cf7134c556b0c8216a48e5336`.
PR #62 is merged at that SHA. PR #63 is open, targets main and has head
`3bd5e5ce4d666fc9dde5b4eddf11caf448a50904`.
The isolated branch `stabilise/taller-2026-10-27` starts at that head and retains
functional repairs in `2303e9347dd9c120fe8f790deae88770b3b5bbd9`.
Cleanup is committed separately from functional changes. Do not merge PR #63
separately if this candidate is integrated. Final merge requires Tomas's approval
of the exact candidate SHA. No release/tag/Homebrew publication is authorised.

## Repository hygiene

Inventory: 746 tracked files before cleanup; reviewed path/mode inventory,
large files, ignored-but-tracked files, packaging selectors and references.

| Path or pattern | Prior state | Classification | Action | Reason | Verification |
| --- | --- | --- | --- | --- | --- |
| `research/urucon2026/results/poster_capture/kivy_user/` | 10 tracked files | D | Untrack, retain locally | Generated Kivy configuration/icons | No runtime or documentation references |
| Other files in `research/urucon2026/results/poster_capture/` | Five PNGs and synthetic v2 replay | F, excluded from workshop | Untrack, retain locally and in source branch | Unreferenced poster staging; no established canonical research role | Not part of 60-trace reference corpus; original commit preserved |
| `docs/code/latex/` | 142 generated files | D | Untrack, retain locally | Doxygen print intermediates, including obsolete backup-class pages | No maintained external references; Doxygen configuration retained |
| `docs/code/html/` | Generated HTML and supporting assets | C | Retain | Existing published API documentation | Contributor guide explicitly maintains generated documentation |
| `research/urucon2026/FINAL_AUDIT.log` | Tracked despite global log ignore | B | Retain with exact ignore exception | Historical research audit evidence | No historical evidence discarded |
| Research corpus, results, ZIPs and manifests | Generated canonical evidence | B | Retain unchanged | Reproducibility and historical provenance | Compare against source candidate |
| `src/assets/`, documentation images and demonstration GIF | Runtime/documentation binaries | A/C | Retain | Runtime and README resources | Release selectors and README references inspected |
| `TODO-notes.md`, `WORK-ADMIN.md` | Maintainer notes | F/A | Retain | User-authored intent and repository policy | Contents inspected |

Ignore additions are anchored to the specific poster staging and print-output
directories. They do not hide research schemas, canonical results or fixtures.
The original checkout and all pre-existing untracked files are preserved.

## Acceptance status

Native connected workshop rehearsal, fresh dependency installation and final
candidate CI are not yet established.
Historical PR #63 results are not candidate acceptance evidence.

## Confirmed packaging defect

The research builder walks the filesystem rather than the Git index. An ignored
poster directory retained locally was still selected for distribution. An
independent temporary-tree regression failed before the fix. The builder now
excludes precisely that staging directory; canonical results remain selected.
This packaging correction is separate from the untracking commit.

## Independent review and regression matrix

The retained PR #62/#63 repairs consolidate strict transport, preserve deterministic
rules, guard retired callbacks, isolate temporary preferences, validate imported
sessions and require process ownership. These contracts justify retaining the
repairs. The current run repeats their tests; it does not claim independent
reproduction of every historical defect. The new independent reproduction is the
research packaging leak above. No gameplay rule or saved-session format changed.

| Boundary | Earlier defect / current contract | Method and result | Remaining uncertainty |
| --- | --- | --- | --- |
| Inference | Fallback/endpoint divergence → shared strict adapter | Wire-level failure/deadline tests PASS; real headless trace PASS | Complete native model-mediated game |
| Standalone editor | Separate management policy → shared service facade and confirmations | Method and wire tests PASS | Actual confirmation/cancellation UI interactions |
| Model selection | Stale completion could overwrite selection → generation guard | Delayed-completion regression PASS | Already-running older warm-up cannot be cancelled; avoid rapid reselection |
| Temporary settings | Incidental saves persisted execution choices → overlay | Isolation/reload/context tests PASS | Failed default-save UX and active-round policy deserve further rehearsal |
| Scheduled gameplay | Queued old turns could run → game/round token checks | Reset/cancellation/scheduled-turn tests PASS | Full native reset during inference |
| Ownership | Port/historical selection treated as ownership → PID/birth-time receipt | Mocked process-identity tests PASS | No real shutdown deliberately attempted |
| Downloads | Startup could pull missing model → explicit confirmed download | Missing-model and confirmation tests PASS | No actual download/delete performed |
| v2/v3 sessions | Permissive imported rules/malformed structures → strict checks | Malformed-input, replay and analyser tests PASS | Native file-picker and restart sequence |
| Research packaging | Filesystem walk included ignored poster state → exact exclusion | New reproduction failed before fix; two packaging tests PASS after | Broad source inclusion retained for runtime closure |

Responsibilities remain: GameBoard owns scheduling; connector owns conversations;
replay engine owns deterministic transitions; history manager owns completed-turn
records; AppConfig owns preferences and overrides; service owns endpoint/lifecycle
policy; validators/verifier own structural and semantic checks; UI owns presentation
and confirmations. The shared transport and service facade reduce policy duplication.
Kivy coordination remains coupled to gameplay. Schema plus semantic validation are
intentional separate responsibilities, not redundant error recovery.

## Verification ledger

Environment: macOS 26.7.1 arm64; Python 3.12.15; Kivy 2.3.1; Modelito 1.4.6;
Ollama Python 0.6.2; pytest 9.1.1; jsonschema 4.26.0. Existing project virtual
environment reused; `python -m pip check` passed. A fresh installation is NOT TESTED.

- Cleanup revision `22f8b31`: `python run_tests.py non-live` — 291 passed,
  2 skipped. An initial restricted-sandbox run had 15 loopback bind errors;
  rerun with loopback permission passed without source changes.
- Packaging correction `e1959bd`: targeted exclusion and extracted research-package
  tests — 2 passed. The exclusion regression failed on its parent before the fix.
- Revision `f3a08f2a23ad5ea95dcf389274caa133cf16cf7d`: native SDL2 Kivy
  application launched and exited after five seconds, with isolated user state
  and automatic service start/stop disabled. This is launch evidence, not visual
  or end-to-end acceptance. Existing KV deprecation/redeclaration warnings remain.
- Same revision: real Ollama server 0.40.10, installed `smollm2:latest`, two requests
  through `run_batllm_research.py --provider ollama --model smollm2:latest --turns 1`.
  `run_batllm_verify.py` accepted both transitions and both response groundings.
  No download, deletion, service stop or explicit model unload was performed.
- Same revision: Pylint 8.84/10; dependency consistency passed. Research regeneration
  runs in a separate copy so historical corpus/results cannot be overwritten.
  That copy has no Git metadata; its `source_revision: null` is explicitly mapped
  to the revision above, not attributed to the historical research implementation.

Final candidate SHA and final check outcomes are recorded in the PR, avoiding a
self-referential commit hash in this file. Commands use an isolated temporary
`BATLLM_HOME` and `KIVY_HOME`; headless tests also set `KIVY_WINDOW=mock`,
`KIVY_NO_ARGS=1`, `KIVY_NO_CONSOLELOG=1`. The full live test runner was not invoked.

## Workshop handoff

Follow [Contributing](CONTRIBUTING.md) for Python 3.12 installation and test commands.
Use [User Guide](USER_GUIDE.md) for the two-player game and analyser workflow.
The tested deterministic teaching alternative is:

```bash
python run_batllm_research.py --provider scripted --output /tmp/workshop-session.json
python run_batllm_verify.py /tmp/workshop-session.json
python run_tests.py non-live
```

This is a headless trace/replay exercise, not normal LLM-driven desktop gameplay;
v3 traces are verified by the CLI, not loaded as desktop v2 sessions.

The GitHub fork API currently lists four personal forks and no organisation fork.
The account belongs to `nexo-developers`, `EpicGames` and `LaboratorioDeMedios`;
membership does not establish control or identify the intended workshop organisation.
Do not create a substitute repository. Tomas must identify the organisation before
fork creation. Use GitHub's genuine fork operation and start from the eventual
approved canonical merge commit, not this unmerged branch.

Coordinator: configure `origin` as the workshop fork and `upstream` as
`https://github.com/krahd/BatLLM.git`; protect the workshop main branch and enable
CI. Never copy production credentials. The Homebrew publish job now explicitly
requires `github.repository == 'krahd/BatLLM'`, so workshop tags skip publication.
Students: open an issue with a reproducible problem, create a named individual/group
branch, make focused commits, run non-live tests and docs checks, and submit a PR
to the workshop fork. A peer reviews behaviour and tests; the coordinator merges.
Fetch upstream regularly and integrate reviewed updates through a coordinator PR.
Propose selected workshop work upstream in separate focused PRs for Tomas's review.

## Decision and deferred work

**CONDITIONAL GO for review; not authorised to merge.** Cleanup and the packaging
correction are independently reversible. Required protection checks are
`ubuntu-latest`, `windows-latest`, `macos-latest` and `Homebrew dry-run`, with strict
up-to-date enforcement. Candidate CI and final upstream freshness must be checked.
No claim is made that the complete 16-step desktop teaching workflow passed.

Remaining conditions: rehearse a complete native two-player round, invalid-output
handling, v2 save/analyser navigation and restart on the instructor Mac; establish
fresh installation; review final candidate CI and exact SHA. The scripted fallback
supports a trace-focused class, not an unqualified promise of desktop readiness.

Deferred P2/P3: transactional failed-save UI behaviour; cancelling already-running
obsolete warm-ups; malformed field-level configuration diagnostics; obsolete HTML
API pages and KV warnings; smaller research runtime closure. No broad refactor was
attempted. Cross-repository administrative status synchronisation remains pending.

## Answers to the release questions

1. Started clean on the PR #63 head recorded above; main and ancestry verified.
2. Retained strict transport, ownership, callback, configuration and schema repairs
   for the contracts described in the matrix.
3. Independently reproduced ignored poster-state inclusion in research packaging.
4. Corrected that inclusion; separately restricted publication to canonical GitHub.
5. Kivy coordination and broad research runtime closure remain; deferred above.
6. Untracked 16 poster files and 142 generated print intermediates.
7. Added precise anchored ignores and an explicit historical-log exception.
8. Runtime assets, canonical corpus, schema and historical packages remain unchanged.
9. Native launch passed; the connected desktop rehearsal remains NOT TESTED.
10. Real headless two-request trace and verification passed with installed smollm2.
11. Automated save/analyser tests pass; native save/navigation/restart NOT TESTED.
12. Isolated tests and process-identity tests pass; real destructive operations untested.
13. Local outcomes are above; final candidate checks belong in the PR ledger.
14. Fresh install, connected native rehearsal, native editor interactions remain open.
15. A documented scripted exercise is available; normal classroom play is conditional.
16. The exact final candidate SHA is recorded in the PR and final handoff.
17. Integration is conditional, and requires explicit approval of that SHA.
