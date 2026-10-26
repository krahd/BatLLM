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

Work in progress. Native connected workshop rehearsal, real-model generation,
fresh dependency installation and candidate CI are not yet established.
Historical PR #63 results are not candidate acceptance evidence.

## Confirmed packaging defect

The research builder walks the filesystem rather than the Git index. An ignored
poster directory retained locally was still selected for distribution. An
independent temporary-tree regression failed before the fix. The builder now
excludes precisely that staging directory; canonical results remain selected.
This packaging correction is separate from the untracking commit.
