# AGENTS.md

Canonical operating instructions for AI coding agents working in this repository. These instructions apply to GitHub Copilot, OpenAI Codex, Anthropic Claude, and compatible agents.

## Repository purpose

BatLLM is a Python/Kivy research, education, and game project for exploring AI-mediated play, prompt quality, LLM behaviour, and local model workflows. Agents must preserve the project's practical, critical, and educational framing while keeping the application runnable across supported platforms.

## Important paths

- `run_batllm.py`: main application launcher.
- `run_game_analyzer.py`: standalone game-analyser launcher.
- `src/`: application source code.
- `src/configs/`: configuration files and defaults.
- `requirements.txt`: Python dependencies.
- `docs/README.md`: canonical project overview.
- `docs/USER_GUIDE.md`: user-facing manual.
- `docs/CONTRIBUTING.md`: developer setup, architecture, and testing guide.
- `docs/ROADMAP.md`: planned product direction.
- `docs/RELEASE_CRITERIA_1_0.md`: release gates.
- `STATUS.md`: complete current project status report; mandatory upkeep.

## Mandatory STATUS.md upkeep

`STATUS.md` must be kept up to date at all times.

Agents must review `STATUS.md` before making changes and update it whenever project state changes. This includes changes to code, architecture, dependencies, configuration, documentation, tests, known issues, setup instructions, pending tasks, release state, or repository structure.

Agents must not finish a task that changes the project without ensuring that `STATUS.md` is accurate.

`STATUS.md` must be a complete project status report, not a short changelog. It must include, where relevant:

- project purpose
- setup and run instructions
- current implementation state
- architecture overview
- important files and directories
- recent changes
- tests and verification status
- known issues, risks, and limitations
- pending tasks
- next steps
- longer-term steps

Timestamp requirements:

- Include a `Last updated` line near the top using exactly this format: `Last updated: YYYY-MM-DD HH:MM`.
- Use local wall-clock time.
- Repeat the exact same `Last updated` line as the final line at the bottom of `STATUS.md`.
- The top and bottom lines must match exactly.
- Treat a stale, missing, mismatched, or incorrectly formatted timestamp as a blocking documentation error.

## Diagrams in STATUS.md

`STATUS.md` should include useful architecture diagram(s) and flow chart(s) as inline SVG when the repository structure, execution flow, or data flow is complex enough to benefit from visual documentation.

SVG requirements:

- Use inline SVG directly in `STATUS.md` when practical.
- Ensure text remains inside boxes and inside the SVG canvas.
- Ensure arrows and connector lines do not pass through unrelated boxes or labels.
- Make the canvas larger when needed for correctness and legibility.
- Prefer generous spacing over compactness.
- Keep labels concise and readable.
- Update diagrams when architecture, data flow, execution flow, or module relationships meaningfully change.
- Avoid trivial diagram updates when no relevant structural change has occurred.

## Communication style

Do not use playful, whimsical, cute, or filler progress phrases.

Do not say things like:

- “combobulating”
- “cooking”
- “thinking...”
- “working on it”
- “let me dive in”
- “I’ll get started”

When doing work, either provide the result directly or, for long tasks, give terse factual status updates only.

Allowed status style:

- “Reading files.”
- “Found the issue.”
- “Applying patch.”
- “Tests passed.”
- “Tests failed: <reason>.”

Do not anthropomorphise the process. Do not perform fake enthusiasm.

Additional communication rules:

- No decorative progress messages.
- No jokes, metaphors, or playful status words.
- No “I’m going to...” unless asking for confirmation.
- Prefer concise technical updates in plain present tense.
- When using tools, report only meaningful findings, blockers, or completed changes.

## Development rules

- Inspect relevant files and tests before editing.
- Prefer small, focused changes over broad rewrites.
- Preserve public behaviour and compatibility unless explicitly asked to change them.
- Do not delete or overwrite user-authored work unless explicitly requested.
- Keep generated artifacts, caches, build outputs, local virtual environments, and temporary files out of git.
- Do not commit secrets, API keys, local credentials, machine-specific absolute paths, or private data.
- Use British English in prose documentation unless a file already follows another convention.
- Keep user-facing documentation aligned with behaviour changes.
- Keep release/version references consistent across all relevant files when changing versions.

## Safety rules

BatLLM can interact with a real local Ollama installation and user-created saved sessions. Treat these as real user state.

- Preserve confirmation prompts for destructive or expensive operations.
- Do not weaken safeguards around model deletion, downloads, local service control, saved-session handling, or configuration writes.
- Do not make tests mutate repository defaults or user configuration unless the test uses an isolated temporary path.
- Be explicit in `STATUS.md` about validation that was not run.

## Validation

Run the narrowest checks that cover the change, then broaden when shared behaviour may be affected. Prefer commands documented in `docs/CONTRIBUTING.md` when present.

Typical checks may include:

```bash
python -m pytest -q
python run_batllm.py
python run_game_analyzer.py
```

Only claim tests passed when they were actually run. Record tests run, tests not run, failures, and external validation gaps in `STATUS.md`.

## Git hygiene

- Check the worktree before and after edits.
- Do not revert user changes unless explicitly requested.
- Stage only intended paths when the worktree is mixed.
- Commit or push only when explicitly requested.
