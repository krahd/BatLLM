# configuration and constants

from kivy.config import Config as KivyConfig
import yaml
from pathlib import Path
import copy

APP_NAME = "BatLLM"
CONFIG_PATH = Path(__file__).parent / "config.yaml"

# Maximize the window on startup
KivyConfig.set('graphics', 'window_state', 'maximized')

# Default fallback values
DEFAULTS = {
    "game": {
        "total_rounds": 3,
        "turns_per_round": 5,
        "independent_models": True,
        "prompt_augmentation": False,
        "initial_health": 20,
        "bullet_damage": 3,
        "shield_size": 20
    },
    "ui": {
        "primary_color": "#ffffff",
        "font_size": 14,
        "frame_rate": 60
    }
}


class AppConfig:
    """This class handles the application configuration.
    It loads the configuration from a YAML file and provides methods to get and set configuration values.
    """    

    config = None
    path = None

    
    def __init__(self, path=CONFIG_PATH):
        self._config = copy.deepcopy(DEFAULTS)
        self._path = path
        self.load(path)



    def load(self, path=CONFIG_PATH):
        """Loads the configuration from the specified path.
        If the file does not exist, it initializes with default values.
        """
        
        if path.exists():
            with open(path, "r") as f:
                user_config = yaml.safe_load(f) or {}
                
                for section, values in user_config.items():
                    if section not in self._config:
                        self._config[section] = {}
                        
                    self._config[section].update(values)







    def save(self, path=CONFIG_PATH):
        """Saves the current configuration to the specified path or the default path.
        If the path is None, it uses the path set during initialization.
        """

        
        if path is None:
            path = self._path
            
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(self._config, f)




    def get(self, section, key):
        """Gets a configuration value from the specified section and key.
        """
        return self._config.get(section, {}).get(key, DEFAULTS.get(section, {}).get(key))



    def set(self, section, key, value):
        """Sets a configuration value for the specified section and key.    
        If the section does not exist, it creates it.
        """
        
        if not isinstance(value, (str, int, float, bool)):
            if section not in self._config:
                self._config[section] = {}
                
        self._config[section][key] = value



    def as_dict(self):
        """Returns the configuration as a dictionary.
        """
        return self._config


# Singleton instance
config = AppConfig()