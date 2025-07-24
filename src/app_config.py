# configuration and constants

from kivy.config import Config as KivyConfig
import yaml
from pathlib import Path
import copy

APP_NAME = "BattleLLM"
CONFIG_PATH = Path(__file__).parent / "configs/config.yaml"

# Maximize the window on startup
KivyConfig.set('graphics', 'window_state', 'maximized')

# Default fallback values
DEFAULTS = {
    "game": {
        "total_rounds": 3,
        "total_turns": 5,
        "independent_models": True,
        "prompt_augmentation": False,
        "initial_health": 20,
        "bullet_damage": 3,
        "shield_size": 20
    },
    "ui": {
        "primary_color": "#ffffff",
        "font_size": 14
    }
}


class AppConfig:
    def __init__(self, path=CONFIG_PATH):
        self._config = copy.deepcopy(DEFAULTS)
        self._path = path
        self.load(path)

    def load(self, path):
        if path.exists():
            with open(path, "r") as f:
                user_config = yaml.safe_load(f) or {}
                for section, values in user_config.items():
                    if section not in self._config:
                        self._config[section] = {}
                    self._config[section].update(values)

    def save(self, path=None):
        if path is None:
            path = self._path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self._config, f)

    def get(self, section, key):
        return self._config.get(section, {}).get(key, DEFAULTS.get(section, {}).get(key))

    def set(self, section, key, value):
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    def as_dict(self):
        return self._config


# Singleton instance
config = AppConfig()

# Convenient top-level access (optional)
TOTAL_ROUNDS = config.get("game", "total_rounds")
TOTAL_TURNS = config.get("game", "total_turns")
INDEPENDENT_MODELS = config.get("game", "independent_models")
PROMPT_AUGMENTATION = config.get("game", "prompt_augmentation")
INITIAL_HEALTH = config.get("game", "initial_health")
BULLET_DAMAGE = config.get("game", "bullet_damage")
SHIELD_SIZE = config.get("game", "shield_size")
PRIMARY_COLOR = config.get("ui", "primary_color")
FONT_SIZE = config.get("ui", "font_size")