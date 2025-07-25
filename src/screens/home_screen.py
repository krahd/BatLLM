
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



#    def on_kv_post(self, base_widget):     
#        """This method is called after the KV rules have been applied."""   
        
#        gbw = self.ids.game_board
#        self.bots = [Bot(id = i, board_widget = gbw) for i in range(1, 3)]  # Create two bot instances
#        gbw.set_bots(self.bots)
#        gbw.render()

        
       

    def load_prompt_from_file(self, player_id, path= "../assets/prompts/prompt_2.txt"):
        prompt_path = Path(__file__).parent / path
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                new_prompt = f.read()
            self.set_prompt_input_text(player_id, new_prompt)
            
        except FileNotFoundError:
            print ("Prompt file not found:", prompt_path)



#    def get_bot_by_id(self, id):
        """Returns the bot instance with the specified ID."""
#        for bot_instance in self.bots:
#            if bot_instance.id == id:
#                return bot_instance
#        return None



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
        
        
           
        
        
      

    # game logic for playing a round
    #def play_round(self):
        """Plays a round of the game with the current bot commands."""
    #    print("Playing round...") # TODO cound rounds
    #    bs = random.sample(self.bots, 2)

    #    turn = 1

       
        # Loop through the turns of the round

        

    #    for turn in range(1, config.get("game", "total_turns")): 

            #TODO update header with turn info
                        
            # Get the commands from both bots
    #        for b in bs:            
    #            b.execute_prompt_in_llm()
  
    #        turn = turn + 1
            # TODO create one window per bot where prompts and commands are shown



            
    #    popup = Popup(title='', content=Label(text='Round Ended'), size_hint=(None, None), size=(400, 400))
        #popup.open()
                                              

      
        
   # def play_turn (self, bots, turn_number):
        """Plays a turn of the game with the current bot commands."""

    #    if turn_number < config.get("game", "total_turns"):
     #       print(f"Playing turn {turn_number}...")
            
      #      for b in bots:            
       #         b.execute_prompt_in_llm()


        #    Clock.schedule_once(lambda dt: self.play_turn(bots, turn_number + 1))
            