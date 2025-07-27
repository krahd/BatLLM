
from pathlib import Path
import datetime
from kivy.uix.screenmanager import Screen
from game.history_manager import HistoryManager
from game.bot import Bot
from kivy.clock import Clock
from game.game_board import GameBoard

 
from configs.app_config import config
from util.util import show_confirmation_dialog, show_text_input_dialog

class HomeScreen(Screen):    
    """A HomeScreen instance is the main screen of the application. 
    It contains the UX components for game control, prompting, and the game board (GameBoard)
    
    Args:
        Screen (_type_): Kivy's base screen class.
            
    """    

    history = None
    
    def __init__(self, **kwargs):     
        """Constructor for the HomeScreen class.
        Initializes the screen and sets up the history manager.
        """           
        super().__init__(**kwargs)
        self.history = HistoryManager()
        
        
    
    def save_session (self):
        """Handler for the save session button.
        Takes care of the user interaction and delegates the actual saving to the GameBoard.
        """        
        def on_saving_confirmed():                        
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            show_text_input_dialog(on_confirm=on_filename_confirmed, title="Save As", default_text=f"session-{timestamp}.json")

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
        """Handler for the start new game button.
        Takes care of the user interaction and delegates the actual logic to GameBoard.
        """        
        
        def _start_new_game():            
            self.ids.game_board.start_new_game()
            self.update_title_label()
            
        show_confirmation_dialog("New Game",
                                 "Abandon current game and start a new one?",
                                 _start_new_game)
    
        
    
    def go_to_settings_screen(self):
        """Handler for the settings button.
        Switches the current screen to the settings screen.
        """        
        self.manager.current = "settings"
       


    def get_prompt_input_text(self, id):
        """Returns the text in the prompt input field for the specified player bot ID.

        Args:
            id (_type_): The bot ID

        Returns:
            _type_: Returns the text int the text input or "" if None
        """        
        
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)

        if text_input:
            return text_input.text
        else:   
            pass         
        return ""



    def set_prompt_input_text(self, id, text):
        """Sets the text of the TextInput for the specified bot ID.

        Args:
            id (_type_): the bot id
            text (_type_): the text to enter
        
        """
        
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            pass
    
        
            
    def get_prompt_history_selected_text(self, id):
        """Returns the text from the TextInput for the prompt history of the specified bot ID.

        Args:
            id (_type_): the bot id

        Returns:
            _type_: the text in the corresponding prompt text input 
        """        
        
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        
        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""



    def prompt_history_add_text(self, id, text):
        """Sets the text of the TextInput for the prompt history of the specified bot ID.

        Args:
            id (_type_): bot id
            text (_type_): text to add to the prompts entered in the UI since the app started
        """        
        
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            pass
        


    def rewind_prompt_history(self, bot_id):
        """Rewinds the prompt history for the specified bot ID.

        Args:
            bot_id (_type_): the bot id
        """        
        b = self.ids.game_board.get_bot_by_id(bot_id)
        b.rewind_prompt_history()    
        self.prompt_history_add_text (bot_id, b.get_current_prompt_from_history())
        

        
    def forward_prompt_history(self, bot_id):
        """Forwards the prompt history for the specified bot ID.

        Args:
            bot_id (_type_): the bot id
        """        
        b = self.ids.game_board.get_bot_by_id(bot_id)
        b.forward_prompt_history()        
        self.prompt_history_add_text (bot_id, b.get_current_prompt_from_history())
        


    def copy_prompt_history_selected_text(self, bot_id):
        """Copies the selected prompt in the history to the prompt input field.

        Args:
            bot_id (_type_): the bot id
        """        
        
        new_prompt = self.get_prompt_history_selected_text(bot_id)
        self.set_prompt_input_text(bot_id, new_prompt)
        
        
    
    def submit_prompt(self, bot_id):
        """Tells the bot to use the text in the input text as the prompt for the upcoming round.

        Args:
            bot_id (_type_): the bot id
        """        
        
        new_prompt = self.get_prompt_input_text(bot_id)
        
        if len(new_prompt) > 0:  # ignore empty prompts
        
            self.prompt_history_add_text(bot_id, new_prompt)
            self.set_prompt_input_text(bot_id, "") # Clear the input field 

            # tell the board to submit the prompt for this bot_id
            gbw = self.ids.game_board
            gbw.submit_prompt (bot_id, new_prompt)
        
        

    def on_request_close(self, *args):
        """Handles the request to close the application.
        Shows a confirmation dialog before closing.
        If the user confirms it offers to save the session to a file 
        """
        show_confirmation_dialog("Exit",
                                 "Are you sure you want to exit?",
                                 _on_exit_confirmed,
                                _on_exit_cancelled)

        
        
    def _on_exit_confirmed(self, *args):
        """Callback for the exit confirmation dialog.
        If the user confirms, it offers to save the session to a file.
        """
        def on_saving_confirmed():
            self.save_session()
            self.manager.app.stop()

        def on_saving_cancelled():
            self.manager.app.stop() 

        show_confirmation_dialog("Save Session",
                                 "Do you want to save the current session before exiting?",
                                    on_saving_confirmed, on_saving_cancelled)
        


    def _on_exit_cancelled(self, *args):
        """Callback for the exit cancellation dialog.
        If the user cancels, it does nothing.
        """
        pass    
        
        

        
        
           
        
        
      

    