from kivy.uix.screenmanager import Screen
from app_config import AppConfig

class HomeScreen(Screen):
    pass

    def save_game (self):
        print ("Saving game...")

    def go_to_settings_screen(self):
        self.manager.current = "settings"