> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Configuration](CONFIGURATION.md) · [Testing](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# Configuration Reference

BatLLM reads its runtime configuration from `src/configs/config.yaml`.

## File Location

- primary runtime config: `src/configs/config.yaml`
- loader: `src/configs/app_config.py`

BatLLM writes updated values back to `src/configs/config.yaml` when the app saves configuration.

## Current Default File

```yaml
data:
  saved_sessions_folder: saved_sessions
game:
  bot_diameter: 0.1
  bot_step_length: 0.03
  bullet_damage: 5
  bullet_diameter: 0.2
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
  max_tokens: null
  model: qwen3:30b
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
  confirm_on_exit: true
  font_size: 16
  frame_rate: 60
  primary_color: '#0b0b0b'
  prompt_save_on_exit: false
  title: BatLLM
```

## Section Reference

### `data`

| Key | Meaning |
| --- | --- |
| `saved_sessions_folder` | Default folder for saved sessions. |

### `game`

| Key | Meaning |
| --- | --- |
| `bot_diameter` | Normalized bot diameter used by the renderer. |
| `bot_step_length` | Default movement step used by `M` and manual movement. |
| `bullet_damage` | Health removed by a successful hit. |
| `bullet_diameter` | Normalized bullet render size. |
| `bullet_step_length` | Bullet movement step size. |
| `independent_contexts` | `true` means each bot keeps separate chat history; `false` means both bots share one history. |
| `initial_health` | Starting health per bot. |
| `prompt_augmentation` | `true` means BatLLM prepends structured game-state data to the player prompt. |
| `shield_initial_state` | Starting shield state for new bots. |
| `shield_size` | Shield arc width in degrees. |
| `total_rounds` | Maximum number of rounds in a game. |
| `turns_per_round` | Maximum number of turns per round. |

### `llm`

| Key | Meaning |
| --- | --- |
| `debug_requests` | Reserved debug flag in the YAML; not a primary user control in the current UI. |
| `max_tokens` | Optional generation option forwarded when not `null`. |
| `model` | Active model name used for gameplay and as the BatLLM-selected Ollama model. |
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
| `timeout` | Optional timeout; if unset, `OllamaConnector` currently falls back to `55`. |
| `top_k` | Optional top-k sampling value. |
| `top_p` | Optional top-p sampling value. |
| `url` | Ollama base URL, usually `http://localhost`. |

Optional advanced key supported by the current code:

| Key | Meaning |
| --- | --- |
| `max_history_messages` | If present, limits the number of retained chat messages. If absent, BatLLM defaults to `turns_per_round * 2`. |

### `ui`

| Key | Meaning |
| --- | --- |
| `confirm_on_exit` | Controls whether the home screen exit flow asks for confirmation. |
| `font_size` | Default font size used by the `markup()` helper in `util.utils`. |
| `frame_rate` | Render/update interval for the game board. |
| `primary_color` | Current theme color value kept in config; not heavily wired into the present Kivy views. |
| `prompt_save_on_exit` | Controls whether BatLLM asks for a save filename before exit. |
| `title` | App window title. |

## Settings Screen Mappings

The Settings screen writes these keys:

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

The Ollama configuration screen writes:

- `llm.model`

## Notes

1. `llm.path` affects gameplay chat requests, not the model-management calls made by the Ollama configuration screen.
2. The Ollama configuration screen assumes the configured host and port are the shared local Ollama service to manage.
3. BatLLM reads the system-instruction file paths directly from config, so broken paths will fail at runtime.
