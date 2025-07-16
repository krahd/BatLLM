from kivy.uix.screenmanager import Screen
from pathlib import Path
import bot


class HomeScreen(Screen):

    bots = [bot.bot(id=i) for i in range(1, 3)]  # Create two bot instances
    
    
    
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
        for bot_instance in self.bots:
            if bot_instance.id == id:
                return bot_instance
        return None


    def get_prompt_text(self, id):
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""

    def set_prompt_text(self, id, text):
        input_id = f"prompt_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            print(f"No TextInput found for id: {input_id}")
            

    def get_prompt_history_text(self, id):
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""

    def set_prompt_history_text(self, id, text):
        input_id = f"prompt_history_player_{id}"
        text_input = self.ids.get(input_id)
        if text_input:
            text_input.text = text
        else:
            print(f"No TextInput found for id: {input_id}")
        
    
    def rewind_prompt_history(self, bot_id):
        b = self.get_bot_by_id(bot_id)
        b.rewind_prompt_history()    
        self.set_prompt_history_text (bot_id, b.get_current_prompt_history())
        
    def forward_prompt_history(self, bot_id):
        b = self.get_bot_by_id(bot_id)
        b.forward_prompt_history()        
        self.set_prompt_history_text (bot_id, b.get_current_prompt_history())


    def copy_prompt_history(self, bot_id):
        b = self.get_bot_by_id(bot_id)
        b.copy_prompt_history()   
        self.set_prompt_text(bot_id, b.get_prompt())
        

    # TODO call this when there's an update on the game
    def render_game(self):
        self.ids.game_board_widget.render()
        

    def submit_prompt(self, bot_id):
        b = self.get_bot_by_id(bot_id)
        new_prompt = self.get_prompt_text(bot_id)
        b.submit_prompt (new_prompt)
        self.set_prompt_history_text(bot_id, b.get_current_prompt_history())
           
        # Clear the input field after submission
        self.set_prompt_text(bot_id, "")