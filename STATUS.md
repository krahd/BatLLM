# BatLLM – Project Status

Last updated: 2026-05-06 23:41

## Project purpose

BatLLM is a free/libre Python/Kivy research, education, and game project for exploring AI-mediated gameplay, prompt quality, LLM behaviour, context design, and local model operation. It provides a turn-based battle game in which players use LLMs to act on their behalf, plus tools for replaying and analysing saved sessions.

## Current implementation state

The repository currently provides:

- main BatLLM gameplay launcher via `run_batllm.py`
- standalone game analyser via `run_game_analyzer.py`
- Kivy-based application code under `src/`
- local Ollama-oriented workflow for model selection, startup, teardown, download, and deletion
- prompt/history/session handling and v2 saved-session replay support
- cross-platform release-bundle generation
- Homebrew packaging support for macOS Apple Silicon
- project documentation under `docs/`

Root-level `AGENTS.md` and `STATUS.md` governance is being introduced so humans and agents have a consistent current-state reference.

## Active focus

Current project focus is stabilising the pre-1.0 application experience, especially first-run behaviour, Ollama configuration, saved-session replay, cross-platform packaging, and documentation alignment.

## Architecture overview

BatLLM is organised as a Python desktop application with documentation and packaging helpers around it. The main launcher starts the Kivy app, which reads configuration from `src/configs/`, interacts with local Ollama tooling, records gameplay/session data, and can hand saved sessions to the analyser.

### Architecture diagram

The diagram summarises the current repository-level architecture.

<svg xmlns="http://www.w3.org/2000/svg" width="980" height="420" viewBox="0 0 980 420" role="img" aria-labelledby="batllm-arch-title batllm-arch-desc">
  <title id="batllm-arch-title">BatLLM architecture overview</title>
  <desc id="batllm-arch-desc">Launchers start the Kivy application and analyser, which use source modules, configuration, saved sessions, Ollama integration, documentation, and packaging helpers.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" />
    </marker>
  </defs>
  <rect x="30" y="40" width="200" height="70" rx="10" fill="none" stroke="black" />
  <text x="130" y="70" text-anchor="middle" font-size="14">run_batllm.py</text>
  <text x="130" y="90" text-anchor="middle" font-size="12">main launcher</text>
  <rect x="30" y="160" width="200" height="70" rx="10" fill="none" stroke="black" />
  <text x="130" y="190" text-anchor="middle" font-size="14">run_game_analyzer.py</text>
  <text x="130" y="210" text-anchor="middle" font-size="12">analyser launcher</text>
  <rect x="310" y="80" width="220" height="90" rx="10" fill="none" stroke="black" />
  <text x="420" y="115" text-anchor="middle" font-size="14">src/ application</text>
  <text x="420" y="137" text-anchor="middle" font-size="12">Kivy UI, game logic,</text>
  <text x="420" y="155" text-anchor="middle" font-size="12">history, sessions</text>
  <rect x="610" y="40" width="230" height="70" rx="10" fill="none" stroke="black" />
  <text x="725" y="70" text-anchor="middle" font-size="14">src/configs/</text>
  <text x="725" y="90" text-anchor="middle" font-size="12">settings and defaults</text>
  <rect x="610" y="145" width="230" height="80" rx="10" fill="none" stroke="black" />
  <text x="725" y="175" text-anchor="middle" font-size="14">Local Ollama</text>
  <text x="725" y="197" text-anchor="middle" font-size="12">models and service</text>
  <rect x="610" y="260" width="230" height="80" rx="10" fill="none" stroke="black" />
  <text x="725" y="290" text-anchor="middle" font-size="14">Saved sessions</text>
  <text x="725" y="312" text-anchor="middle" font-size="12">gameplay replay data</text>
  <rect x="310" y="250" width="220" height="70" rx="10" fill="none" stroke="black" />
  <text x="420" y="280" text-anchor="middle" font-size="14">docs/ and packaging</text>
  <text x="420" y="300" text-anchor="middle" font-size="12">guides, bundles, Homebrew</text>
  <line x1="230" y1="75" x2="310" y2="115" stroke="black" marker-end="url(#arrow)" />
  <line x1="230" y1="195" x2="310" y2="145" stroke="black" marker-end="url(#arrow)" />
  <line x1="530" y1="115" x2="610" y2="75" stroke="black" marker-end="url(#arrow)" />
  <line x1="530" y1="135" x2="610" y2="185" stroke="black" marker-end="url(#arrow)" />
  <line x1="530" y1="155" x2="610" y2="300" stroke="black" marker-end="url(#arrow)" />
  <line x1="420" y1="170" x2="420" y2="250" stroke="black" marker-end="url(#arrow)" />
</svg>

### Flow chart

The flow chart shows the normal local gameplay and analysis loop.

<svg xmlns="http://www.w3.org/2000/svg" width="980" height="360" viewBox="0 0 980 360" role="img" aria-labelledby="batllm-flow-title batllm-flow-desc">
  <title id="batllm-flow-title">BatLLM gameplay flow</title>
  <desc id="batllm-flow-desc">A player launches BatLLM, configures the game and model, submits prompts, receives model commands, advances rounds, saves sessions, and optionally replays them in the analyser.</desc>
  <defs>
    <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" />
    </marker>
  </defs>
  <rect x="30" y="130" width="130" height="70" rx="10" fill="none" stroke="black" />
  <text x="95" y="160" text-anchor="middle" font-size="13">Launch</text>
  <text x="95" y="180" text-anchor="middle" font-size="12">BatLLM</text>
  <rect x="210" y="130" width="150" height="70" rx="10" fill="none" stroke="black" />
  <text x="285" y="157" text-anchor="middle" font-size="13">Configure game</text>
  <text x="285" y="178" text-anchor="middle" font-size="12">and Ollama</text>
  <rect x="410" y="130" width="150" height="70" rx="10" fill="none" stroke="black" />
  <text x="485" y="157" text-anchor="middle" font-size="13">Submit prompt</text>
  <text x="485" y="178" text-anchor="middle" font-size="12">with context</text>
  <rect x="610" y="130" width="150" height="70" rx="10" fill="none" stroke="black" />
  <text x="685" y="157" text-anchor="middle" font-size="13">Parse command</text>
  <text x="685" y="178" text-anchor="middle" font-size="12">and update game</text>
  <rect x="810" y="130" width="140" height="70" rx="10" fill="none" stroke="black" />
  <text x="880" y="157" text-anchor="middle" font-size="13">Save session</text>
  <text x="880" y="178" text-anchor="middle" font-size="12">or continue</text>
  <rect x="610" y="255" width="150" height="65" rx="10" fill="none" stroke="black" />
  <text x="685" y="282" text-anchor="middle" font-size="13">Replay in</text>
  <text x="685" y="302" text-anchor="middle" font-size="12">analyser</text>
  <line x1="160" y1="165" x2="210" y2="165" stroke="black" marker-end="url(#flow-arrow)" />
  <line x1="360" y1="165" x2="410" y2="165" stroke="black" marker-end="url(#flow-arrow)" />
  <line x1="560" y1="165" x2="610" y2="165" stroke="black" marker-end="url(#flow-arrow)" />
  <line x1="760" y1="165" x2="810" y2="165" stroke="black" marker-end="url(#flow-arrow)" />
  <path d="M 880 200 L 880 230 L 685 230 L 685 255" fill="none" stroke="black" marker-end="url(#flow-arrow)" />
  <path d="M 685 130 L 685 85 L 485 85 L 485 130" fill="none" stroke="black" marker-end="url(#flow-arrow)" />
</svg>

## Setup and run instructions

macOS/Linux:

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python3 -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -r requirements.txt
python run_batllm.py
```

Windows:

```powershell
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
py -m venv .venv_BatLLM
.\.venv_BatLLM\Scripts\Activate.ps1
pip install -r requirements.txt
python run_batllm.py
```

Standalone analyser:

```bash
python run_game_analyzer.py
```

## Configuration and environment variables

- `src/configs/`: application configuration and defaults.
- `requirements.txt`: Python dependency list.
- local Ollama CLI/service: required for the default local-model workflow.
- `llm.model` and `llm.last_served_model`: documented model-selection settings in the project README.
- `BATLLM_HOME`: Homebrew install uses this user-writable directory; default is `~/Library/Application Support/BatLLM`.

## Important files and directories

- `run_batllm.py`: main app launcher.
- `run_game_analyzer.py`: standalone analyser launcher.
- `src/`: application source.
- `src/configs/`: configuration files.
- `docs/README.md`: canonical overview and quick start.
- `docs/USER_GUIDE.md`: user manual.
- `docs/CONTRIBUTING.md`: developer guide.
- `docs/ROADMAP.md`: planned 1.0 and 2.0 direction.
- `docs/RELEASE_CRITERIA_1_0.md`: 1.0 release gates.
- `create_release_bundles.py`: cross-platform bundle generator.
- `create_homebrew_formula.py`: Homebrew formula generator.
- `scripts/cmr-r`: convenience wrapper for local launch.

## Recent changes

- Added root-level agent governance instructions.
- Added this root-level status report snapshot.
- Current documentation describes BatLLM `0.3.2` as the active repository version line.
- Current documentation describes modelito-backed Ollama service helper migration and single-Ollama workflow work as already present in recent commits.

## Tests and verification status

Not run while creating this documentation-only snapshot.

The repository documentation describes test and validation workflows in `docs/CONTRIBUTING.md`; future implementation changes should run the narrowest relevant checks and record them here.

## Known issues, risks, and limitations

- Local Ollama operations affect the user's real local Ollama installation.
- Cross-platform release launchers require platform-specific validation.
- Saved-session replay intentionally targets v2 session envelopes; legacy top-level list exports are rejected.
- Some current-state details should be refreshed after a full code and test audit.

## Pending tasks

- Review `docs/CONTRIBUTING.md` and align this status report with its exact validation commands.
- Confirm current version metadata across `VERSION`, docs, package/build files, and release helpers.
- Replace any remaining placeholder or stale documentation found during the next repository audit.

## Next steps

1. Run the documented test suite and record results here.
2. Verify first-run behaviour with a clean config directory.
3. Validate the analyser against representative v2 saved-session exports.

## Longer-term steps

1. Complete explicit 1.0 release criteria.
2. Continue tightening cross-platform packaging validation.
3. Keep documentation focused on current user and maintainer workflows.

## Decisions and rationale

- BatLLM remains centred on local, practical, AI-mediated gameplay rather than direct manual control.
- The default workflow assumes local Ollama integration, with clear warnings because model and service operations have real effects.
- `STATUS.md` is now the canonical current-state snapshot for agents and human maintainers.

---

Last updated: 2026-05-06 23:41
