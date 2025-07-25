import random

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget

from kivy.uix.label import Label
from kivy.uix.popup import Popup

from normalized_canvas import NormalizedCanvas

from app_config import config
from bot import Bot

from widgets.game_board_ux import _on_keyboard_down


class GameBoardWidget(Widget):
	
	bots = []
	bulletTrace = []
	bullet_alpha = 1
	snd_shoot = None # TODO move to Bot class
	snd_hit = None # TODO move to Bot class
	current_turn = None
	current_round = None
	shuffled_bots = None
 
	def __init__(self, **kwargs):
		super(GameBoardWidget, self).__init__(**kwargs)
		
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
		self._keyboard.bind(on_key_down = _on_keyboard_down)
		
		self.bind(size=self._redraw, pos=self._redraw)

		self.bulletTrace = []  # Initialize bullet trace list
		self.bullet_alpha = 1  # Initialize bullet alpha value		

		self.snd_shoot = SoundLoader.load("assets/sounds/shoot1.wav") # TODO move to Bot class
		self.snd_hit = SoundLoader.load("assets/sounds/bot_hit.wav") # TODO move to Bot class		

		self.current_turn = None
		self.current_round = None		
		self.shuffled_bots = None
  
		Clock.schedule_interval(self._redraw, 1.0 / config.get("ui", "frame_rate")) 



	def set_bots(self, bots):
		self.bots = bots


			
	def on_kv_post(self, base_widget):
		"""This method is called after the KV rules have been applied."""
		super().on_kv_post(base_widget)

		# Create two bot instances with reference to this GameBoardWidget
		self.bots = [Bot(id = i, board_widget = self) for i in range(1, 3)]
		



	def _keyboard_closed(self): # virtual keyboard closed handler
		print('keyboard have been closed!')
		self._keyboard.unbind(on_key_down = self._on_keyboard_down)
		self._keyboard = None




	def _redraw(self, *args):
		self.render()



			
	def render(self, *args):      
		"""Renders the game board and all bots."""              
		self.canvas.clear()
		
		# keep bots inside bounds
		for bot in self.bots:
			r = bot.diameter / 2
			
			if bot.x < r:
				bot.x = r
			elif bot.x > 1 - r:
				bot.x = 1 - r
			
			if bot.y < r:
				bot.y = r
			elif bot.y > 1 - r:   
				bot.y = 1 - r
		
		with NormalizedCanvas(self):
			c = 1
			Color(c, c, c, 1)
			Rectangle(pos=(0, 0), size=(1, 1))
			c = .2
			Color(c, c, c, .6)
			Line(rectangle=(0, 0, 1, 1), width=0.001)

			for bot in self.bots:
				bot.render()

			for (x, y) in self.bulletTrace:
				Color (1, 0, 0, self.bullet_alpha)  # Red color for bullet trace
				Ellipse(pos=(x - 0.005, y - 0.005), size=(0.005, 0.005))
				if (self.bullet_alpha > 0):
					self.bullet_alpha -= 0.01  # Decrease alpha for fading effect
				else:
					self.bulletTrace.clear()
			   

		
			
						
	# mouse button down event handler    
	def on_touch_down(self, touch):
		"""Handles mouse click events on the game board."""
		if self.collide_point(touch.x, touch.y):         
			nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
			
			for bot in self.bots:
				print ("-- " , bot.x)
			
			return True   
				
		return super().on_touch_down(touch)  



	# mouse drag event handler
	def on_touch_move(self, touch):
		"""Handles mouse drag events on the game board."""
		if self.collide_point(touch.x, touch.y):
			nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
		   
			return True
		
		return super().on_touch_move(touch)



	def find_id_in_parents(self, target_id):
		parent = self.parent
		while parent:
			if hasattr(parent, 'ids') and target_id in parent.ids:
				return parent.ids[target_id]
			parent = parent.parent
		return None




	def add_llm_response_to_history(self, bot_id, command):
		"""Adds a command to the output history box for the specified bot."""  

        #TODO move this function to the HomeScreen class	
		box = self.find_id_in_parents(f"output_history_player_{bot_id}")
   
		if box is not None:
			box.text += f"{len(box.text.splitlines()) + 1}. {command}\n"
		else:
			print(f"Could not find output history box for bot_id: {bot_id}")



	def submit_prompt(self, bot_id, new_prompt):
		"""Submits the prompt for the specified bot."""
		
		bot = self.get_bot_by_id(bot_id)
		bot.prepare_prompt_submission(new_prompt)

		if all(b.ready_to_submit_prompt_to_llm for b in self.bots):
			self.play_round()



	def play_round(self):
		self.current_turn = 0
		print(f"Playing round {self.current_round}") # TODO count rounds

		# shuffle bots for this round
		self.shuffled_bots = random.sample(self.bots, 2)
		self.play_turn()
		

	def play_turn(self):
		if not self.current_turn < config.get("game", "turns_per_round"):
		
			round_res = "b1 health: " + str(self.bots[0].health) + "\n" + \
						"b2 health: " + str(self.bots[1].health)
	
			popup = Popup(title=f'Round {self.current_round} ended', content=Label(text = round_res), size_hint = (None, None), size = (400, 400))
			popup.open()			
			return

		print(f"Playing turn {self.current_turn}...")
		for b in self.shuffled_bots:            
			b.submit_prompt_to_llm()
		
		

	def on_bot_llm_interaction_complete(self, bot):
		"""Callback when a bot's LLM interaction is complete."""
  
		print(f"Bot {bot.id} interaction complete.")

		self.turn_index = (self.turn_index + 1) % len(self.bots) # ++ every 2
  
		Clock.schedule_once(self.play_turn, 0)
      
			
      				


	def get_bot_by_id(self, id):
		"""Returns the bot instance with the specified ID."""
		for bot_instance in self.bots:
			if bot_instance.id == id:
				return bot_instance
		return None