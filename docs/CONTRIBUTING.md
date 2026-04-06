> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# Contributing

This is BatLLM's developer and contribution manual. It covers how to set up the project locally, how the codebase is organised, how to validate changes, and what is expected when contributing code or documentation.

BatLLM is both a software project and a research and education project. When contributing, preserve the practical software quality of the repository and the project's framing around AI literacy, human-AI mediation, and hands-on learning.

## Roadmap

Features wishlist: [ROADMAP.md](ROADMAP.md)

## Ways To Contribute

Contributions are welcome in several forms:

- bug fixes
- new features
- documentation improvements
- testing improvements
- design, UX, and workflow clean-up
- analysis of recorded game histories and model behaviour

If you are unsure whether an idea fits the project, opening an issue first is a good default.

## Contribution Rules

- keep pull requests scoped to one topic
- use English commit messages
- explain non-obvious changes in the pull request description
- update documentation when the workflow, UI, setup, configuration, or tests change
- keep the FAQ focused on recurring non-trivial questions; routine walkthrough material belongs in the user guide
- keep cross-platform impact in mind when changing scripts, paths, or dependencies

## Development Setup

### Python Environment

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python3 -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -r requirements.txt
```

Use Python 3.10 or newer. Python 3.11 or 3.12 is recommended.

On Windows:

```powershell
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
py -m venv .venv_BatLLM
.\.venv_BatLLM\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ollama Environment

The codebase depends on two different Ollama surfaces:

- the Python `ollama` package for gameplay chat requests
- the `ollama` CLI for the local service-management helpers and the Ollama config screen

For non-live unit work, the CLI is not required. For live gameplay or `run_tests.py full`, it is required.

### Running The App Locally

```bash
python run_batllm.py
```

For the standalone analyzer:

```bash
python run_game_analyzer.py
```

If Ollama is not already installed, either install it manually from the official download page for your platform or let BatLLM launch the official installer flow:

- macOS: `https://ollama.com/download`
- Linux: `https://ollama.com/download/linux`
- Windows: `https://ollama.com/download/windows`

## Repository Layout

Core runtime modules:

- `src/main.py`: Kivy app entrypoint
- `src/view/`: screens and `.kv` layouts
- `src/game/game_board.py`: match flow, rendering hooks, and UI coordination
- `src/game/bot.py`: bot state and command execution
- `src/game/bullet.py`: bullet movement and collision logic
- `src/game/ollama_connector.py`: chat/history request builder using the Python `ollama` client
- `src/game/history_manager.py`: authoritative game and chat history
- `src/game/replay_engine.py`: Kivy-free replay and rules helpers shared by gameplay and the analyzer
- `src/game/session_schema.py`: saved-session schema validation and v2 envelope helpers
- `src/ollama_service.py`: cross-platform Ollama lifecycle helper used by the app and test runner
- `src/analyzer_main.py`: standalone Game Analyzer app entrypoint
- `src/analyzer_model.py`: session navigation and replay-step model for the analyzer UI
- `src/configs/`: YAML config files and config loader
- `run_batllm.py`: repository-root launcher
- `run_game_analyzer.py`: repository-root standalone analyzer launcher
- `run_tests.py`: cross-platform test runner
- `create_release_bundles.py`: source and platform bundle generator
- `start_ollama.sh` and `stop_ollama.sh`: Unix wrappers around the Python Ollama helper

Maintained documentation:

- `docs/README.md`
- `docs/USER_GUIDE.md`
- `docs/CONTRIBUTING.md`
- `docs/FAQ.md`
- `docs/CHANGELOG.md`
- `docs/CREDITS.md`

Generated API docs:

- `docs/code/`

## Architecture Overview

The current gameplay stack works like this:

1. `HomeScreen` owns the high-level UI and delegates game actions to `GameBoard`.
2. `GameBoard` owns the active `Bot` instances, the prompt store, and the live round/turn flow.
3. `Bot` instances execute movement, rotation, shield, and bullet actions.
4. `GameBoard` uses `OllamaConnector` to send synchronous chat requests through the Python `ollama` client.
5. `HistoryManager` records game history and chat history as the single source of truth.

The current replay/analyzer stack works like this:

1. `HistoryManager.save_session()` exports the v2 saved-session envelope.
2. Each round records a frozen `gameplay_settings_snapshot`.
3. `replay_engine.py` replays ordered plays against the saved round snapshot instead of the live config.
4. `AnalyzerSessionModel` turns those replay results into timeline steps, state diffs, and inspector text.
5. `AnalyzerLoadScreen` and `AnalyzerReviewScreen` expose the replay in-app and through `run_game_analyzer.py`.

The current model-management stack works like this:

1. `OllamaConfigScreen` checks server state using local HTTP endpoints such as `/api/version`, `/api/ps`, and `/api/tags`.
2. It uses `src/ollama_service.py` for cross-platform service lifecycle actions.
3. It uses `https://ollama.com/library` as the remote-library source for downloadable model names.
4. It uses `/api/pull` and `/api/generate` for pull and preload operations.

Important implementation notes:

- `NormalizedCanvas` keeps arena drawing resolution-independent by treating positions as values in the range `0.0` to `1.0`.
- `HistoryManager` is the single source of truth for game and chat history.
- `util.paths` is responsible for resolving assets, prompts, config-relative files, and save folders without relying on the current working directory.
- BatLLM is currently built around two-player AI-mediated play, and some UI assumptions still rely on that structure.

## Configuration Reference

BatLLM reads its runtime configuration from `src/configs/config.yaml`.

### File Locations

- primary runtime config: `src/configs/config.yaml`
- loader: `src/configs/app_config.py`

BatLLM writes updated values back to `src/configs/config.yaml` when the app saves configuration.

### Current Default File

```yaml
data:
  saved_sessions_folder: saved_sessions
game:
  bot_diameter: 0.1
  bot_step_length: 0.03
  bullet_damage: 5
  bullet_diameter: 0.02
  bullet_step_length: 0.01
  independent_contexts: true
  initial_health: 30
  prompt_augmentation: true
  shield_initial_state: true
  shield_size: 70
  total_rounds: 2
  turns_per_round: 8
llm:
  debug_requests: false
  last_served_model: qwen3:30b
  max_tokens: null
  model: qwen3:30b
  model_timeouts: {}
  num_ctx: 4096
  num_predict: null
  num_thread: null
  path: /api/chat
  port: 11434
  seed: null
  stop: null
  system_instructions_augmented_independent: src/assets/system_instructions/augmented_independent_1.txt
  system_instructions_augmented_shared: src/assets/system_instructions/augmented_shared_1.txt
  system_instructions_not_augmented_independent: src/assets/system_instructions/not_augmented_independent_1.txt
  system_instructions_not_augmented_shared: src/assets/system_instructions/not_augmented_shared_1.txt
  temperature: null
  timeout: null
  top_k: null
  top_p: null
  url: http://localhost
ui:
  auto_start_ollama: false
  stop_ollama_on_exit: false
  confirm_on_exit: true
  font_size: 16
  frame_rate: 60
  primary_color: '#0b0b0b'
  prompt_save_on_exit: false
  title: BatLLM
```

### Section Reference

#### `data`

| Key | Meaning |
| --- | --- |
| `saved_sessions_folder` | Default folder for saved sessions. |

Saved sessions exported from the current app use the v2 BatLLM envelope. The analyzer depends on that format and rejects legacy top-level list exports.

#### `game`

| Key | Meaning |
| --- | --- |
| `bot_diameter` | Normalised bot diameter used by the renderer. |
| `bot_step_length` | Default movement step used by `M` and manual movement. |
| `bullet_damage` | Health removed by a successful hit. |
| `bullet_diameter` | Normalised bullet render size. |
| `bullet_step_length` | Bullet movement step size. |
| `independent_contexts` | `true` means each bot keeps separate chat history; `false` means both bots share one history. |
| `initial_health` | Starting health per bot. |
| `prompt_augmentation` | `true` means BatLLM prepends structured game-state data to the player prompt. |
| `shield_initial_state` | Starting shield state for new bots. |
| `shield_size` | Shield arc width in degrees. |
| `total_rounds` | Maximum number of rounds in a game. |
| `turns_per_round` | Maximum number of turns per round. |

#### `llm`

| Key | Meaning |
| --- | --- |
| `debug_requests` | Reserved debug flag in the YAML; not a primary user control in the current UI. |
| `last_served_model` | The last model BatLLM explicitly warmed so startup can restore it. |
| `max_tokens` | Optional generation option forwarded when not `null`. |
| `model` | Active model name used for gameplay and as the BatLLM-selected Ollama model. |
| `model_timeouts` | Optional per-model timeout overrides keyed by installed model name. |
| `num_ctx` | Optional Ollama context size. |
| `num_predict` | Optional generation limit. |
| `num_thread` | Optional thread-count override. |
| `path` | Chat path used by BatLLM gameplay requests. Current default is `/api/chat`. |
| `port` | Ollama service port. |
| `seed` | Optional generation seed. |
| `stop` | Optional stop sequence setting. |
| `system_instructions_augmented_independent` | File used when prompt augmentation is on and contexts are independent. |
| `system_instructions_augmented_shared` | File used when prompt augmentation is on and context is shared. |
| `system_instructions_not_augmented_independent` | File used when prompt augmentation is off and contexts are independent. |
| `system_instructions_not_augmented_shared` | File used when prompt augmentation is off and context is shared. |
| `temperature` | Optional generation temperature. |
| `timeout` | Optional global timeout fallback used when there is no per-model override. |
| `top_k` | Optional top-k sampling value. |
| `top_p` | Optional top-p sampling value. |
| `url` | Ollama base URL, usually `http://localhost`. |

Optional advanced key supported by the current code:

| Key | Meaning |
| --- | --- |
| `max_history_messages` | If present, limits the number of retained chat messages. If absent, BatLLM defaults to `turns_per_round * 2`. |

#### `ui`

| Key | Meaning |
| --- | --- |
| `confirm_on_exit` | Controls whether the home screen exit flow asks for confirmation. |
| `font_size` | Default font size used by the `markup()` helper in `util.utils`. |
| `frame_rate` | Render/update interval for the game board. |
| `auto_start_ollama` | When true, BatLLM can start Ollama automatically during app startup. |
| `stop_ollama_on_exit` | When true, BatLLM can stop Ollama automatically during app shutdown. |
| `primary_color` | Current theme colour value kept in config; not heavily wired into the present Kivy views. |
| `prompt_save_on_exit` | Controls whether BatLLM asks for a save filename before exit. |
| `title` | App window title. |

### Screen Mappings

The settings screen writes these keys:

- `game.total_rounds`
- `game.turns_per_round`
- `game.initial_health`
- `game.bullet_damage`
- `game.shield_size`
- `game.bot_step_length`
- `game.independent_contexts`
- `game.prompt_augmentation`
- `ui.confirm_on_exit`
- `ui.prompt_save_on_exit`
- `ui.auto_start_ollama`
- `ui.stop_ollama_on_exit`

The Ollama configuration screen writes:

- `llm.model`
- `llm.model_timeouts`
- installer actions are launched from the screen, but the config file is not modified directly by that action

### Configuration Notes

1. `llm.path` affects gameplay chat requests, not the model-management calls made by the Ollama configuration screen.
2. The Ollama configuration screen assumes the configured host and port are the shared local Ollama service to manage.
3. BatLLM reads the system-instruction file paths directly from config, so broken paths will fail at runtime.
4. The current Ollama lifecycle toggles are stored in `ui.auto_start_ollama` and `ui.stop_ollama_on_exit`. `main.py` still accepts the legacy `ui.auto_stop_ollama` key as a backward-compatible fallback for older configs.
5. `llm.last_served_model` tracks the last model BatLLM explicitly warmed so startup can restore that serving state.
6. Timeout precedence is: `llm.model_timeouts[model]`, then `llm.timeout`, then BatLLM's built-in common-model defaults, then the generic fallback.

## Testing And Validation

BatLLM has three practical test tiers:

1. shell/config smoke checks
2. headless non-live unit tests
3. live Ollama smoke tests

### Environment

Use the project virtual environment:

```bash
source .venv_BatLLM/bin/activate
```

For terminal-only environments, run Kivy tests headlessly:

```bash
export KIVY_WINDOW=mock
export KIVY_NO_ARGS=1
export KIVY_NO_CONSOLELOG=1
export KIVY_HOME=/tmp/batllm-kivy
export PYTHONPATH=src
```

### Quick Smoke

`run_tests.py core` is the cross-platform smoke runner:

```bash
python run_tests.py core
```

`run_tests.sh core` remains available as a Unix convenience wrapper around the same flow.

The quick smoke currently runs only the lightweight smoke checks in `src/tests/test_history_compact.py`:

```bash
./run_tests.sh core
```

That covers:

- config shape
- shell-script syntax
- source compilation

### Recommended Non-Live Unit Suite

This is the most useful day-to-day test command for UI and logic changes:

```bash
python -m pytest -q src/tests/test_history_compact.py src/tests/test_close_prompt_behavior.py src/tests/test_utils_confirmation_dialog.py src/tests/test_ollama_config_screen.py src/tests/test_ollama_config_screen_logic.py src/tests/test_multiplatform_support.py
```

That suite covers:

- exit-flow behaviour
- confirmation and text-input pop-ups
- Ollama config screen logic
- model-picker behaviour
- cross-platform launch and path handling
- non-live smoke checks

### Live Ollama Smoke

`run_tests.py full` starts Ollama, runs the full `src/tests` suite with live Ollama smoke enabled, and then stops Ollama:

```bash
python run_tests.py full
```

`run_tests.sh full` remains available on Unix-like shells as a wrapper around the same command:

```bash
./run_tests.sh full
```

Equivalent environment toggle for the live smoke tests:

```bash
BATLLM_RUN_OLLAMA_SMOKE=1 PYTHONPATH=src ./.venv_BatLLM/bin/python -m pytest -q src/tests
```

Use this only when:

- the Ollama CLI is installed
- the configured host and port are available
- you are comfortable with BatLLM starting and stopping the configured local Ollama service

### Documentation Validation

When docs or API surface change:

```bash
doxygen docs/code/dox_config.properties
```

Review the generated diff under `docs/code/` before committing.

### What To Run For Common Changes

| Change type | Minimum recommended validation |
| --- | --- |
| gameplay logic | non-live unit suite |
| exit flow or pop-ups | non-live unit suite |
| Ollama config screen | non-live unit suite |
| cross-platform smoke | `python run_tests.py core` |
| Ollama integration path | non-live unit suite plus live smoke if possible |
| docs only | regenerate code docs if public API docs changed |

## Documentation Workflow

BatLLM's docs are split by role:

- `README.md`: project framing plus the high-level map for users and contributors
- `USER_GUIDE.md`: user-facing game manual
- `FAQ.md`: shared high-signal reference for recurring user and contributor questions
- `CONTRIBUTING.md`: developer-facing setup, architecture, configuration, testing, and troubleshooting

When behaviour changes, update the maintained docs in the same branch. In particular, update docs when you change:

- UI labels
- setup steps
- config keys or defaults
- test commands
- Ollama model-management behaviour
- keyboard and exit behaviour
- project-level framing, aims, or educational positioning

Do not use the FAQ for trivial click-path questions unless the behaviour is surprising, high-risk, or easy to misinterpret. Keep the FAQ focused on questions whose answers help users compete more effectively or help contributors reason about the codebase.

## Release Workflow

BatLLM now uses tags for versions and a repository-level `VERSION` file to track the current release number.

To build release assets:

```bash
python create_release_bundles.py
```

That produces:

- source archives
- a Windows bundle with `.bat` launchers
- a macOS bundle with `.command` launchers
- a Linux bundle with `.sh` launchers

## Coding Conventions

- use Python 3 style annotations where practical
- keep Kivy screen logic in the screen classes and layout structure in `.kv` files
- avoid undocumented user-facing behaviour changes
- prefer clear state transitions over hidden side effects
- use British English in maintained documentation
- keep identifiers, API names, and other code-level naming consistent with the existing codebase

## Pull Request Workflow

Recommended contribution flow:

1. fork the repository and clone it locally
2. create a branch for one topic only
3. make the change with relevant tests or validation
4. update docs if the workflow, UI, or developer process changed
5. review the resulting diff, including generated documentation noise
6. open a pull request with a clear description of what changed and why

Before opening a PR:

1. run the relevant tests
2. update docs if the workflow or UI changed
3. regenerate code docs if public modules or screen docs changed
4. review the resulting diff for generated-file noise before pushing

### Documentation Review Checklist

- confirm visible UI labels in the docs match the current Kivy labels and button text
- confirm config keys and defaults mentioned in docs match `src/configs/config.yaml` and `src/configs/app_config.py`
- confirm compatibility and version references still match `VERSION`, current platform support, and release naming
- confirm screenshots, diagrams, and screen descriptions still match the current interface, or remove them if they no longer do
- confirm cross-links, setup commands, and platform-specific launcher notes still point to maintained files and workflows

## Developer Troubleshooting

### The App Cannot Start Ollama

Symptoms:

- `Start Ollama` fails
- the output log says `ollama not found`
- the install confirmation prompt appears

What to check:

1. confirm the `ollama` CLI is installed and available on your `PATH`
2. run `ollama --version` in a terminal
3. verify `llm.url` and `llm.port` in `src/configs/config.yaml`

### Gameplay Fails To Talk To The Model

BatLLM gameplay uses the Python `ollama` package plus the configured chat endpoint.

Check:

1. `pip install -r requirements.txt` completed successfully
2. the virtual environment contains the `ollama` Python package
3. `llm.path` is correct for the server you are using
4. the configured model name in `llm.model` exists locally

### The Remote Model List Will Not Load

The remote picker fetches model names from `https://ollama.com/library`.

If refresh fails:

1. verify the machine has outbound network access
2. retry from the Ollama screen
3. check the Ollama screen output log for the captured error

Existing local selections are preserved if the remote refresh fails.

### The Local Model List Is Empty

The local picker loads from `/api/tags` on the configured Ollama host.

Check:

1. Ollama is actually running on `llm.url:llm.port`
2. `ollama list` shows models in the same installation
3. the configured host and port point to the intended local service

### Doxygen Output Is Stale

Regenerate the code docs from the repository root:

```bash
doxygen docs/code/dox_config.properties
```

### `run_tests.sh core` Does Not Cover My UI Change

That is expected. `core` only runs the lightweight smoke checks. Use the non-live unit suite above for screen and pop-up changes.
