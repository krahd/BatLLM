
from pathlib import Path

from kivy.uix.screenmanager import Screen
from history_manager import HistoryManager
from bot import Bot
from kivy.clock import Clock
from widgets.game_board import GameBoardWidget
from app_config import config
from util import show_confirmation_dialog, show_filename_dialog

class HomeScreen(Screen):    

    history = None

    
    def __init__(self, **kwargs):        
        super(HomeScreen, self).__init__(**kwargs)
        self.history = HistoryManager()
        
        
    
    def save_session (self):
        def on_saving_confirmed():            
            show_filename_dialog(on_confirm=on_filename_confirmed)

        def on_filename_confirmed(filename):
            if filename:
                self.ids.game_board.save_session(filename)                
            else:
                pass

        def on_saving_cancelled():
            pass

        
        
        show_confirmation_dialog("Save Session",
                                 "Are you sure you want to save the session?",
                                    on_saving_confirmed, on_saving_cancelled)

        
                                 

        
    def start_new_game(self):
        
        def _start_new_game():
            print("Starting a new game...")
            self.ids.game_board.start_new_game()
            
        show_confirmation_dialog("New Game",
                                 "Abandon current game and start a new one?",
                                 _start_new_game)
                                 
        
        

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
        
        b = self.ids.game_board.get_bot_by_id(bot_id)
        b.rewind_prompt_history()    
        self.prompt_history_add_text (bot_id, b.get_current_prompt_from_history())
        

        
    def forward_prompt_history(self, bot_id):
        """Forwards the prompt history for the specified bot ID."""
        b = self.ids.game_board.get_bot_by_id(bot_id)
        b.forward_prompt_history()        
        self.prompt_history_add_text (bot_id, b.get_current_prompt_from_history())
        


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
        
        
           
        
        
      

    