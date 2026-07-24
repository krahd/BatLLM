> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [Roadmap](ROADMAP.md) · [1.0 Criteria](RELEASE_CRITERIA_1_0.md) · [Status](../STATUS.md)**

# UI unification plan for 1.0

This plan records the remaining work needed to make gameplay and the Game Analyzer feel like one application. It is a release-planning document, not a claim that visual parity is complete.

## Principles

- Equivalent actions should use equivalent labels.
- Back, cancel, and `Esc` behaviour should be predictable.
- Status and error messages should use one severity vocabulary.
- Layout consistency should not obscure the distinct purposes of gameplay and analysis.
- Keyboard and accessibility behaviour should be documented and tested where practical.

## Workstream 1: navigation and headers

Current state:

- Major navigation actions exist and use recognisable labels.
- Gameplay, analyzer load, and analyzer review screens still use different header and spacing structures.

Before 1.0:

- verify screen titles and back actions on all primary screens;
- remove contradictory or duplicated navigation controls; and
- decide whether a shared header component is required for 1.0 or explicitly deferred.

## Workstream 2: control vocabulary

Current state:

- Common actions such as **Load**, **Save**, **Back**, **Cancel**, and **Use Selected** are documented consistently.

Before 1.0:

- review all user-facing button text against the User Guide;
- align confirmation and failure wording; and
- keep destructive operations visually distinct.

## Workstream 3: layout and visual rhythm

Current state:

- Gameplay and analyzer screens are usable but do not share one complete spacing and typography system.

Before 1.0:

- review section spacing, panel grouping, text hierarchy, and state summaries;
- remove layout-specific instructions from documentation unless users genuinely need them; and
- defer deep theme-module refactoring only with explicit sign-off.

## Workstream 4: keyboard and accessibility behaviour

Current state:

- `Esc` handling is deterministic for the main settings and modal flows covered by tests.
- The application still relies primarily on pointer interaction.

Before 1.0:

- manually verify `Esc` and back behaviour on every main screen;
- ensure focus and modal dismissal remain understandable; and
- record any keyboard-first limitations in release notes.

## Acceptance criteria

- A new user can move between gameplay, settings, history, Ollama configuration, and analysis without guessing how to return.
- Equivalent actions do not use contradictory names.
- Destructive operations require clear confirmation.
- The User Guide matches the shipped labels and navigation.
- Deferred visual work is explicit and does not hide functional inconsistency.
