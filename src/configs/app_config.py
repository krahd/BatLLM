"""Configuration loader module"""
import copy
from pathlib import Path

import yaml
from kivy.config import Config as KivyConfig

from util.paths import resolve_config_path

APP_NAME = "BatLLM"
SHIPPED_CONFIG_PATH = Path(__file__).parent / "config.yaml"
CONFIG_PATH = resolve_config_path(SHIPPED_CONFIG_PATH)

# Maximize the window on startup
KivyConfig.set("graphics", "window_state", "maximized")

# Default fallback values
DEFAULTS = {
    "game": {
        "total_rounds": 2,
        "turns_per_round": 8,
        "independent_contexts": True,
        "prompt_augmentation": True,
        "initial_health": 30,
        "bullet_damage": 5,
        "bullet_diameter": 0.02,
        "shield_size": 70,
    },
    "ui": {
        "font_size": 16,
        "frame_rate": 60,
        "confirm_on_exit": True,
        "prompt_save_on_exit": False,
        "auto_start_ollama": False,
        "stop_ollama_on_exit": False,
    },
    "llm": {
        "last_served_model": "",
        "timeout": None,
        "model_timeouts": {},
    },
}


def _read_yaml(path: Path) -> dict:
    """Read a YAML mapping, returning an empty mapping for missing or empty files."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def _merge_config(target: dict, overlay: dict) -> None:
    """Merge a sectioned config mapping into the target mapping."""
    for section, values in overlay.items():
        if section not in target:
            target[section] = {}
        if isinstance(values, dict):
            target[section].update(values)
        else:
            target[section] = values


def load_config_data(
    path: Path | None = None,
    *,
    shipped_path: Path = SHIPPED_CONFIG_PATH,
) -> dict:
    """Load defaults, then the shipped config, then an optional user overlay config."""
    resolved_path = resolve_config_path(shipped_path) if path is None else path
    merged = copy.deepcopy(DEFAULTS)
    _merge_config(merged, _read_yaml(shipped_path))
    if resolved_path != shipped_path:
        _merge_config(merged, _read_yaml(resolved_path))
    return merged


class AppConfig:
    """This class handles the application configuration.
    It loads the configuration from a YAML file and provides methods to get and set configuration values.
    """

    def __init__(self, path: Path | None = None, default_path: Path = SHIPPED_CONFIG_PATH):
        self._default_path = default_path
        self._config = copy.deepcopy(DEFAULTS)
        self._path = resolve_config_path(default_path) if path is None else path
        self.load(self._path)


    def load(self, path: Path | None = None):
        """Loads the configuration from the specified path.
        If the file does not exist, it initialises with default values.
        """
        resolved_path = resolve_config_path(self._default_path) if path is None else path
        self._path = resolved_path
        self._config = load_config_data(resolved_path, shipped_path=self._default_path)



    def save(self, path: Path | None = None):
        """Saves the current configuration to the specified path or the default path.
        If the path is None, it uses the path set during initialisation.
        """

        if path is None:
            path = self._path

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._config, f, sort_keys=False)



    def get(self, section, key):
        """Gets a configuration value from the specified section and key."""
        return self._config.get(section, {}).get(
            key, DEFAULTS.get(section, {}).get(key)
        )


    def set(self, section, key, value):
        """Sets a configuration value for the specified section and key.
        If the section does not exist, it creates it.
        """

        if not isinstance(value, (str, int, float, bool)):
            if section not in self._config:
                self._config[section] = {}

        self._config[section][key] = value


    def as_dict(self):
        """Returns the configuration as a dictionary."""
        return self._config


# Singleton instance
config = AppConfig()
