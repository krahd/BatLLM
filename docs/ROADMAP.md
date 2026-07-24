> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [Status](../STATUS.md) · [1.0 Criteria](RELEASE_CRITERIA_1_0.md) · [Contributing](CONTRIBUTING.md)**

# Roadmap

BatLLM's current priority is a stable local desktop release. The core game, saved-session analysis, deterministic replay helpers, local Ollama integration, cross-platform launchers, and research runtime already exist. The remaining 1.0 work is release hardening rather than a new game design.

Version 2.0 is the planned architectural change towards networked play and additional clients.

## 1.0: stable local desktop release

### Goals

- Make first-run setup understandable for non-specialist users.
- Make gameplay and analysis feel like one coherent application.
- Preserve deterministic game, session, and replay behaviour.
- Release with defensible cross-platform and packaging validation.

### Remaining work

- Complete native first-run testing on macOS, Linux, and Windows.
- Finish the interface-consistency work in [UI_UNIFICATION_PLAN_1_0.md](UI_UNIFICATION_PLAN_1_0.md).
- Improve recovery and messages for missing, stopped, slow, or non-responsive Ollama states.
- Validate release-bundle state locations and move them to platform user directories if needed before 1.0.
- Complete install-level Apple Silicon Homebrew validation.
- Continue testing malformed model output, timeouts, save/load compatibility, and analyzer edge cases.
- Sign off the [1.0 release criteria](RELEASE_CRITERIA_1_0.md) and [first-run checklist](FIRST_RUN_RELEASE_CHECKLIST.md).

### Not in scope for 1.0

- client-server migration;
- networked play;
- web clients;
- central prompt or game repositories; and
- single-player or NPC modes.

## 2.0: networked play architecture

### Goals

- Move from a desktop-only process to a service-backed platform.
- Support remote human-vs-human play without losing deterministic replay.
- Make the game engine usable by desktop and web clients.

### Planned sequence

1. Separate remaining game/session coordination from Kivy-bound UI code.
2. Define a versioned server contract for game creation, prompt submission, turn execution, session storage, and replay retrieval.
3. Preserve state-transition tests and schema compatibility during the split.
4. Implement networked desktop play.
5. Add a web client after the server and desktop behaviours agree.
6. Consider shared prompt and game repositories only after authentication, moderation, provenance, and versioning are designed.

The server contract comes before new clients. Shared repositories are optional later 2.x work, not a prerequisite for networked play.
