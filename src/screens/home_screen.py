import random
from kivy.uix.screenmanager import Screen
from pathlib import Path
import bot
from kivy.uix.popup import Popup
from kivy.uix.label import Label


class HomeScreen(Screen):



    bots = []
    augment_prompts = None  # TODO get from config
    total_rounds = None
    total_turns = None
    initial_health = None
    bullet_damage = None
    shield_size = None
    independent_models = None
    prompt_augmentation = None


    def __init__(self, **kwargs):        
        super(HomeScreen, self).__init__(**kwargs)
        gbw = self.ids.game_board
        self.bots = [bot.Bot(id = i, board_widget = gbw) for i in range(1, 3)]  # Create two bot instances
        gbw.add_bots(self.bots)
        self.augment_prompts = False  # TODO get from config
        self.total_rounds = 10  # TODO get from config
        self.total_turns = 14  # TODO get from config
        self.initial_health = 100  # TODO get from config
        self.bullet_damage = 10  # TODO get from config
        self.shield_size = 45  # TODO get from config
        self.independent_models = True  # TODO get from config -- needs to be implemented still
        self.prompt_augmentation = False  # TODO get from config
        


    def on_enter(self):
        settings_screen = self.manager.get_screen("settings")
        self.total_rounds = settings_screen.total_rounds
        self.total_turns = settings_screen.total_turns
        self.initial_health = settings_screen.initial_health
        self.bullet_damage = settings_screen.bullet_damage
        self.shield_size = settings_screen.shield_size
        self.independent_models = settings_screen.independent_models
        self.prompt_augmentation = settings_screen.prompt_augmentation  


        """
            total_rounds = NumericProperty(config.get("game", "total_rounds"))        
            total_turns = NumericProperty(config.get("game", "total_turns"))
            initial_health = NumericProperty(config.get("game", "initial_health"))
            bullet_damage = NumericProperty(config.get("game", "bullet_damage"))
            shield_size = NumericProperty(config.get("game", "shield_size"))
            independent_models = BooleanProperty(config.get("game", "independent_models"))
            prompt_augmentation = BooleanProperty(config.get("game", "prompt_augmentation"))
        """


    
    def save_game (self):
        print ("Saving game...(TODO)")
        # TODO
        


    def go_to_settings_screen(self):
        self.manager.current = "settings"



    def on_kv_post(self, gbw, *args):        
        gbw = self.ids.game_board
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
        round_turns = 14 # TODO get round count from config
        # Loop through the turns of the round        

        for turn in range(1, round_turns): 

            print ("Turn: ", turn)                
            
            # Get the commands from both bots
            for b in bs:            
                b.execute_prompt_in_llm()

  
            turn = turn + 1
            # TODO create one window per bot where prompts and commands are shown
            
        popup = Popup(title='', content=Label(text='Round Ended'), size_hint=(None, None), size=(400, 400))
        popup.open()
                                              

      
        
        