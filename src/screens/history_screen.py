from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, BooleanProperty
from configs.app_config import config


class HistoryScreen(Screen):
    """
    History screen to display the history of commands and responses.
    """   


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        



    def update(self, bot_id, log_s, hist_s):
        """
        Updates the history screen with the given bot id and log.
        
        Args:
            bot_id (int): The id of the bot.
            string_log_temp (str): The log string to display.
            history (list): The history of comands and responses.
        """
       
        self.ids.title_label.text = f"History for Bot {bot_id}"
        self.ids.string_panel.text = log_s
        self.ids.history_panel.text = hist_s



    def go_back_home(self):
        """Switches the current screen to the home screen.
        """
        self.manager.current = "home"   
