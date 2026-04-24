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

### 2) Shared Control Vocabulary

- align button labels for load/save/back/cancel flows
- standardize status text tone and severity wording

### 3) Shared Layout Rhythm

- normalize spacing, section headers, and panel grouping
- align prompt and response text treatment where possible

### 4) Shared Accessibility and Keyboard Behavior

- ensure Esc behavior is predictable and documented on all major screens
- ensure primary actions have clear keyboard-first paths where relevant

## Acceptance Criteria

- a contributor can map equivalent actions across gameplay and analyzer without guessing
- no screen uses contradictory labels for the same operation
- keyboard escape and back behavior is consistent for equivalent modal/navigation contexts
- docs screenshots/text match the shipped UX labels
