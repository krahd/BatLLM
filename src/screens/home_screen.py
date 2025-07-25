
from pathlib import Path

from kivy.uix.screenmanager import Screen

from bot import Bot
from kivy.clock import Clock
from widgets.game_board import GameBoardWidget
from app_config import config


class HomeScreen(Screen):    
    def __init__(self, **kwargs):        
        super(HomeScreen, self).__init__(**kwargs)
        
        
    
    def save_game (self):
        print ("Saving game...(TODO)")
        # TODO save the game history for future processing
        


    def go_to_settings_screen(self):
        self.manager.current = "settings"
       

    def load_prompt_from_file(self, player_id, path= "../assets/prompts/prompt_2.txt"):
        prompt_path = Path(__file__).parent / path
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                new_prompt = f.read()
            self.set_prompt_input_text(player_id, new_prompt)
            
        except FileNotFoundError:
            print ("Prompt file not found:", prompt_path)


    def get_prompt_input_text(self, id):
        """Returns the text from the TextInput for the specified bot ID."""
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)

        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""



    def set_prompt_input_text(self, id, text):
        """Sets the text of the TextInput for the specified bot ID."""
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            print(f"No TextInput found for id: {input_id}")


            
    def get_prompt_history_selected_text(self, id):
        """Returns the text from the TextInput for the prompt history of the specified bot ID."""
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        
        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""



    def prompt_history_add_text(self, id, text):
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
        self.prompt_history_add_text (bot_id, b.get_current_prompt_history())
        

        
    def forward_prompt_history(self, bot_id):
        """Forwards the prompt history for the specified bot ID."""
        b = self.get_bot_by_id(bot_id)
        b.forward_prompt_history()        
        self.prompt_history_add_text (bot_id, b.get_current_prompt_history())
        


    def copy_prompt_history_selected_text(self, bot_id):
        """Copies the selected prompt in the history to the prompt input field."""
        new_prompt = self.get_prompt_history_selected_text(bot_id)
        self.set_prompt_input_text(bot_id, new_prompt)
        
        
    # tells the bot to submit the prompt to the LLM
    def submit_prompt(self, bot_id):
        """Submits the prompt for the specified bot ID."""
        
        new_prompt = self.get_prompt_input_text(bot_id)
        self.prompt_history_add_text(bot_id, new_prompt)
        self.set_prompt_input_text(bot_id, "") # Clear the input field 

        # tell the board to submit the prompt for this bot_id
        gbw = self.ids.game_board
        gbw.submit_prompt (bot_id, new_prompt)
        
        
           
        
        
      

    