import random
from pathlib import Path

from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager

from bot import Bot
from screens.settings_screen import SettingsScreen
from widgets.game_board import GameBoardWidget
from app_config import config


class HomeScreen(Screen):
    bots = []

    def __init__(self, **kwargs):        
        super(HomeScreen, self).__init__(**kwargs)
        
        
        
    def get_total_rounds_from_settings(self):
        """
        Gets the value of total_rounds from the SettingsScreen instance
        in the same manager as this screen.
        """
        try:
            # Get the screen manager (self.manager is set by Kivy)            
            sm = self.manager if self.manager is not None else self.get_screen_manager()
                
            settings_screen = sm.get_screen("settings")
            
            return settings_screen.total_rounds
        
        except Exception as e:
            print("Exception type:", type(e).__name__)
            print("Exception message:", str(e))
            print("Could not get total_rounds from SettingsScreen, returning default")


        
    
    def save_game (self):
        print ("Saving game...(TODO)")
        # TODO implement saving game state
        


    def go_to_settings_screen(self):
        self.manager.current = "settings"



    def on_kv_post(self, base_widget):        
        
        gbw = self.ids.game_board
        self.bots = [Bot(id = i, board_widget = gbw) for i in range(1, 3)]  # Create two bot instances
        gbw.add_bots(self.bots)
        gbw.render()

        
       

    def load_prompt_from_file(self, player_id, path= "../assets/prompts/prompt_2.txt"):
        prompt_path = Path(__file__).parent / path
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                new_prompt = f.read()
            self.set_prompt_text(player_id, new_prompt)
            
        except FileNotFoundError:
            print ("Prompt file not found:", prompt_path)



    def get_bot_by_id(self, id):
        """Returns the bot instance with the specified ID."""
        for bot_instance in self.bots:
            if bot_instance.id == id:
                return bot_instance
        return None



    def get_prompt_text(self, id):
        """Returns the text from the TextInput for the specified bot ID."""
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)

        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""



    def set_prompt_text(self, id, text):
        """Sets the text of the TextInput for the specified bot ID."""
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            print(f"No TextInput found for id: {input_id}")


            
    def get_prompt_history_text(self, id):
        """Returns the text from the TextInput for the prompt history of the specified bot ID."""
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""



    def set_prompt_history_text(self, id, text):
        """Sets the text of the TextInput for the prompt history of the specified bot ID."""
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            print(f"No TextInput found for id: {input_id}")
        


    def rewind_prompt_history(self, bot_id):
        """Rewinds the prompt history for the specified bot ID."""
        b = self.get_bot_by_id(bot_id)
        b.rewind_prompt_history()    
        self.set_prompt_history_text (bot_id, b.get_current_prompt_history())
        

        
    def forward_prompt_history(self, bot_id):
        """Forwards the prompt history for the specified bot ID."""
        b = self.get_bot_by_id(bot_id)
        b.forward_prompt_history()        
        self.set_prompt_history_text (bot_id, b.get_current_prompt_history())
        


    def copy_prompt_history(self, bot_id):
        """Copies the current prompt history to the clipboard for the specified bot ID."""
        b = self.get_bot_by_id(bot_id)
        b.copy_prompt_history()   
        self.set_prompt_text(bot_id, b.get_prompt())
        
        
    # tells the bot to submit the prompt to the LLM
    def submit_prompt(self, bot_id):
        """Submits the prompt for the specified bot ID."""
        b = self.get_bot_by_id(bot_id)
        new_prompt = self.get_prompt_text(bot_id)

        # Toggle the augment_promts flag in the bot
        self.get_bot_by_id(bot_id).augment_prompt(self.augment_prompts)
        
        b.submit_prompt (new_prompt)
        self.set_prompt_history_text(bot_id, b.get_current_prompt_history())
           
        # Clear the input field 
        self.set_prompt_text(bot_id, "")

        if all(b.prompt_submitted for b in self.bots):
            self.play_round()


    # game logic for playing a round
    def play_round(self):
        """Plays a round of the game with the current bot commands."""
        print("Playing round...") # TODO cound rounds
        bs = random.sample(self.bots, 2)

        turn = 1
       
        # Loop through the turns of the round        

        for turn in range(1, config.get("game", "total_turns")): 

            #TODO update header with turn info
                        
            # Get the commands from both bots
            for b in bs:            
                b.execute_prompt_in_llm()
  
            turn = turn + 1
            # TODO create one window per bot where prompts and commands are shown
            
        popup = Popup(title='', content=Label(text='Round Ended'), size_hint=(None, None), size=(400, 400))
        popup.open()
                                              

      
        
        