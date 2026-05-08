> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# UI Unification Plan for 1.0

This document breaks the roadmap UX-unification goal into implementable work items.

## Objectives

- make gameplay and analyzer feel like one product
- reduce context switching cost between modes
- keep keyboard and button semantics consistent

## Workstreams

### 1) Shared Navigation and Header

- align top-level navigation affordances between Home, Analyzer Load, and Analyzer Review
- standardize back behavior and screen-title placement

Status: partially complete for 1.0.

- Done for 1.0: equivalent major navigation actions are present and labeled across gameplay/analyzer flows (`Back`, open/load flows, screen-title headers).
- Deferred to 1.1: full shared header component and strict visual parity between gameplay and analyzer top bars.

### 2) Shared Control Vocabulary

- align button labels for load/save/back/cancel flows
- standardize status text tone and severity wording

Status: complete for 1.0 acceptance criteria.

- Done for 1.0: shared action labels are aligned for equivalent operations (`Load`, `Save`, `Back`, `Cancel`) and no contradictory wording remains in maintained UX docs.
- Deferred to 1.1: deeper tone harmonisation for all status/help copy across every screen.

### 3) Shared Layout Rhythm

- normalize spacing, section headers, and panel grouping
- align prompt and response text treatment where possible

Status: partially complete for 1.0.

- Done for 1.0: panel/grouping structure is stable and usable across gameplay/analyzer without contradictory control placement.
- Deferred to 1.1: full spacing/typography consolidation and migration of gameplay screen styling to a central theme module.

### 4) Shared Accessibility and Keyboard Behavior

- ensure Esc behavior is predictable and documented on all major screens
- ensure primary actions have clear keyboard-first paths where relevant

Status: complete for 1.0 acceptance criteria.

- Done for 1.0: Escape handling in modal prompt-loading flow is deterministic and covered by regression tests.
- Deferred to 1.1: additional keyboard-first shortcuts beyond current modal/navigation parity.

## 1.0 Gate Snapshot (2026-05-08)

- Pass for 1.0: Workstreams 2 and 4.
- Pass with explicit deferment to 1.1: Workstreams 1 and 3.
- 1.1 carry-over scope: shared header component, full visual-system consolidation, gameplay-theme modularisation.

## Acceptance Criteria

- a contributor can map equivalent actions across gameplay and analyzer without guessing
- no screen uses contradictory labels for the same operation
- keyboard escape and back behavior is consistent for equivalent modal/navigation contexts
- docs screenshots/text match the shipped UX labels
