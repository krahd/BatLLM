from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, BooleanProperty
from configs.app_config import config


class SettingsScreen(Screen):
    """A screen for configuring game settings.

    Args:
        Screen (_type_): Kivy's base screen class.
    """    
    
    total_rounds = NumericProperty(config.get("game", "total_rounds"))
    turns_per_round = NumericProperty(config.get("game", "turns_per_round"))
    initial_health = NumericProperty(config.get("game", "initial_health"))
    bullet_damage = NumericProperty(config.get("game", "bullet_damage"))
    shield_size = NumericProperty(config.get("game", "shield_size"))
    independent_contexts = BooleanProperty(config.get("game", "independent_contexts"))
    prompt_augmentation = BooleanProperty(config.get("game", "prompt_augmentation"))



    def set_as_defaults(self):
        """Sets the configuration values to the default values defined in app_config.py.
        """
        self.update_config()
        config.save()
        self.go_to_home_screen()        



    def update_config(self):
        """Updates the configuration with the values from the sliders and checkboxes.
        """

        # TODO should settings changes be stored in HistoryManager?
   
        config.set("game", "total_rounds", int(self.ids.rounds_slider.value))
        config.set("game", "turns_per_round", int(self.ids.turns_slider.value))
        config.set("game", "initial_health", int(self.ids.health_slider.value))
        config.set("game", "bullet_damage", int(self.ids.damage_slider.value))
        config.set("game", "shield_size", int(self.ids.shield_slider.value))        
        config.set("game", "independent_contexts", self.ids.independent_checkbox.active)
        config.set("game", "prompt_augmentation", self.ids.augmentation_checkbox.active)
            


    def set_and_return(self):
        """Updates the configuration and returns to the home screen.
        """
        self.update_config()
        self.go_to_home_screen()


    def go_to_home_screen(self):
        """Switches the current screen to the home screen.
        """
        self.manager.current = "home"