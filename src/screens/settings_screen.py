from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, BooleanProperty
from app_config import config


class SettingsScreen(Screen):
    
    total_rounds = NumericProperty(config.get("game", "total_rounds"))
    total_turns = NumericProperty(config.get("game", "total_turns"))
    initial_health = NumericProperty(config.get("game", "initial_health"))
    bullet_damage = NumericProperty(config.get("game", "bullet_damage"))
    shield_size = NumericProperty(config.get("game", "shield_size"))
    independent_models = BooleanProperty(config.get("game", "independent_models"))
    prompt_augmentation = BooleanProperty(config.get("game", "prompt_augmentation"))



    def set_as_defaults(self):
        """Sets the configuration values to the default values defined in app_config.py.
        """
        self.update_config()
        config.save()



    def update_config(self):
        """Updates the configuration with the values from the sliders and checkboxes.
        """
   
        config.set("game", "total_rounds", int(self.ids.rounds_slider.value))
        config.set("game", "total_turns", int(self.ids.turns_slider.value))
        config.set("game", "initial_health", int(self.ids.health_slider.value))
        config.set("game", "bullet_damage", int(self.ids.damage_slider.value))
        config.set("game", "shield_size", int(self.ids.shield_slider.value))        
        config.set("game", "independent_models", self.ids.independent_checkbox.active)
        config.set("game", "prompt_augmentation", self.ids.augmentation_checkbox.active)
        
        print("[Settings] Configurations saved to config.yaml")


    def set_and_return(self):
        self.update_config()
        self.go_to_home_screen()


    def go_to_home_screen(self):
        self.manager.current = "home"