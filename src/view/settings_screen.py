from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, BooleanProperty
from configs.app_config import config
from util.utils import switch_screen


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
    bot_step_length = NumericProperty(config.get("game", "bot_step_length"))
    independent_contexts = BooleanProperty(config.get("game", "independent_contexts"))
    prompt_augmentation = BooleanProperty(config.get("game", "prompt_augmentation"))
    confirm_on_exit = BooleanProperty(config.get("ui", "confirm_on_exit"))
    prompt_save_on_exit = BooleanProperty(config.get("ui", "prompt_save_on_exit"))

    def on_pre_enter(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)
        Window.bind(on_key_down=self.handle_window_key_down)

    def on_pre_leave(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)

    def handle_window_key_down(self, _window, key, *_args):
        if key != 27:
            return False

        self.cancel_and_return()
        return True

    def cancel_and_return(self):
        self.go_to_home_screen()




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
        config.set("game", "bot_step_length", round(float(self.ids.step_slider.value), 2))
        config.set("game", "independent_contexts", self.ids.independent_checkbox.active)
        config.set("game", "prompt_augmentation", self.ids.augmentation_checkbox.active)
        config.set("ui", "confirm_on_exit", self.ids.confirm_on_exit_checkbox.active)
        config.set("ui", "prompt_save_on_exit", self.ids.save_on_exit_checkbox.active)



    def set_and_return(self):
        """Updates the configuration and returns to the home screen.
        """
        self.update_config()
        self.go_to_home_screen()


    def go_to_home_screen(self):
        """Switches the current screen to the home screen.
        """
        switch_screen(self.manager, "home", direction="right")

    def go_to_ollama_config_screen(self):
        """Switches to the Ollama configuration screen."""
        switch_screen(self.manager, "ollama_config", direction="left")
