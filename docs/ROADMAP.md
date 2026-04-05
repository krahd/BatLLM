# ROADMAP

BatLLM is approaching 1.0 as a stable local desktop product. The current 0.2.x line already includes the core game loop, session saving, replay analysis, cross-platform launchers, and Ollama integration, so the remaining work for 1.0 is product consistency, reliability, and release hardening.

Version 2.0 is the planned architecture shift. It should focus on networked play first, then use that foundation to support additional clients and shared content.


## 1.0 - Stable Local Desktop Release

### 1.0 Goals

- Deliver a coherent local-first experience for non-technical users.
- Make the gameplay and analyzer flows feel like one product.
- Release with stronger reliability, onboarding, and test coverage.

### 1.0 Planned Work

- Unify the Game and Analyzer user interface.
- Standardize theme, spacing, typography, button styles, and navigation patterns.
- Align status panels, player summaries, and action controls across screens.
- Harden Ollama integration for offline service, slow startup, missing models, malformed responses, and timeouts.
- Improve user-facing error messages and recovery paths during setup and play.
- Polish session save/load and analyzer replay workflows.
- Preserve compatibility of saved sessions and replay behavior.
- Tighten release bundles, launcher behavior, and first-run setup guidance on macOS, Linux, and Windows.
- Expand tests for failure paths, save/load compatibility, analyzer flows, and cross-platform startup confidence.
- Define explicit 1.0 release criteria for local play, analyzer workflow, onboarding, and documentation.

### 1.0 Not in Scope

- Client-server migration.
- Networked play.
- Web clients.
- Centralized prompt repository.
- Centralized game repository.


## 2.0 - Networked Play Architecture

### 2.0 Goals

- Move BatLLM from a desktop-only app to a client-server platform.
- Support networked play without losing deterministic replay and session analysis.
- Enable additional clients, starting with the web.

### 2.0 Planned Work

- Extract core game execution, replay, and session logic from Kivy-bound UI code.
- Preserve deterministic replay and schema versioning during the refactor.
- Introduce server-side APIs for game creation, prompt submission, turn execution, session storage, and replay retrieval.
- Implement networked clients for remote single-player or remote-hosted play.
- Build a web client once desktop and server behavior are aligned.
- Design centralized prompt and game repositories on top of the server platform.
- Only ship shared repositories after authentication, moderation, versioning, and sync behavior are clearly defined.

### 2.0 Release Ordering

- Engine and service extraction comes before any new client work.
- Networked play is the primary 2.0 deliverable.
- Web access follows the server contract.
- Shared repositories are optional 2.x work if they put 2.0 delivery at risk.
