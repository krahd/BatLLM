import random

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget

from kivy.uix.label import Label
from kivy.uix.popup import Popup

from normalized_canvas import NormalizedCanvas
import os

from app_config import config
from bot import Bot
from history_manager import HistoryManager
from util import show_fading_alert



class GameBoardWidget(Widget):
	
	bots = []
	bulletTrace = []
	bullet_alpha = 1
	snd_shoot = None # TODO move to Bot class, or better to a singleton SoundManager class
	snd_hit = None # TODO move to Bot class, or better to a singleton SoundManager class
	current_turn = None
	current_round = None
	shuffled_bots = None
	games_started = None
	history_manager = None
 
	def __init__(self, **kwargs):
		super(GameBoardWidget, self).__init__(**kwargs)
		
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
		self._keyboard.bind(on_key_down = self._on_keyboard_down)
		
		self.bind(size=self._redraw, pos=self._redraw)

		self.bulletTrace = []  # Initialize bullet trace list
		self.bullet_alpha = 1  # Initialize bullet alpha value		

		self.snd_shoot = SoundLoader.load("assets/sounds/shoot1.wav")
		self.snd_hit = SoundLoader.load("assets/sounds/bot_hit.wav") 

		self.current_turn = None
		self.current_round = None		
		self.shuffled_bots = None
		self.games_started = 0

		self.history_manager = HistoryManager()  # Create the session history manager
		# render loop
		Clock.schedule_interval(self._redraw, 1.0 / config.get("ui", "frame_rate")) 





	def start_new_game(self):
		# reset values
		self.current_turn = None
		self.current_round = None		
		self.shuffled_bots = None
  
     
     	# Create two bot instances with reference to this GameBoardWidget
		self.bots = [Bot(id = i, board_widget = self) for i in range(1, 3)]

		if self.games_started > 0:
			for b in self.bots:
				self.add_text_to_llm_response_history(b.id, "\n\nNew Game\n\n")
				b.ready_for_next_round = False  # need a new prompt for a new round

		self.games_started += 1

		self.history_manager.start_game(self)
		


	def save_session(self, filename):
		folder = f"{config.get("data", "saved_sessions_folder")}"		
		os.makedirs(folder, exist_ok=True)

		filepath = os.path.join(folder, filename)
		print ("saving session to", filepath)
		self.history_manager.save_session(filepath)
		print ("done")

		print (self.history_manager.to_text())


   
	def on_kv_post(self, base_widget):
		"""This method is called after the KV rules have been applied."""
		super().on_kv_post(base_widget)

		self.start_new_game()

		
		


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
			   

		
			
						
	# mouse button down event handler - it does nothing as of now.
	def on_touch_down(self, touch):
		"""Handles mouse click events on the game board."""
		if self.collide_point(touch.x, touch.y):         
			nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
			return True   
				
		return super().on_touch_down(touch)  



	# mouse drag event handler - it does nothing as of now.
	def on_touch_move(self, touch):
		"""Handles mouse drag events on the game board."""
		if self.collide_point(touch.x, touch.y):
			nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
		   
			return True
		
		return super().on_touch_move(touch)



	def find_id_in_parents(self, target_id):  # TODO move to util class
		parent = self.parent
		while parent:
			if hasattr(parent, 'ids') and target_id in parent.ids:
				return parent.ids[target_id]
			parent = parent.parent
		return None



	def add_text_to_llm_response_history(self, bot_id, text):
		 #TODO move this function to the HomeScreen class?
		box = self.find_id_in_parents(f"output_history_player_{bot_id}")
   
		if box is not None:
			box.text += text
		else:
			print(f"Could not find output history box for bot_id: {bot_id}")

	def add_llm_response_to_history(self, bot_id, command):
		"""Adds a command to the output history box for the specified bot."""  
		text = f"   {self.current_turn}. {command}\n" 
		self.add_text_to_llm_response_history(bot_id, text)
        



	def submit_prompt(self, bot_id, new_prompt):
		"""Submits the prompt for the specified bot."""
		
		bot = self.get_bot_by_id(bot_id)
		bot.prepare_prompt_submission(new_prompt)

		if all(b.ready_for_next_round for b in self.bots):
			self.play_round()



	def play_round(self):
		self.current_turn = 0
  
		if self.current_round is None:
			self.current_round = 0

		self.current_round += 1				

		for b in self.bots:
			self.add_text_to_llm_response_history(b.id, f"\nRound {self.current_round}.\n")
			b.ready_for_next_round = False  # need a new prompt for a new round

		# shuffle bots for this coming round
		self.shuffled_bots = random.sample(self.bots, 2)

		self.history_manager.start_round(self)	
		
		self.play_turn(0)
		self.history_manager.end_turn(self)



	def game_over(self):
		"""Checks if the game is over."""
  
		for b in self.bots:
			if b.health <= 0:				
				return True
		if self.current_round >= config.get("game", "total_rounds"):			
			return True

		return False

   
		


	def play_turn(self, dt):
     
		if not self.current_turn < config.get("game", "turns_per_round"):  # round's over

			self.history_manager.end_round(self)
   
			round_res = "\n"
   
			if (self.game_over()):
				self.history_manager.end_game(self)				
    
				round_res += "Final Results:\n"
				for b in self.bots:
					round_res += f"Bot {b.id}'s health: {b.health}\n\n"
     
				popup = Popup(title='Game Over', content=Label(text = round_res), size_hint = (None, None), size = (400, 400))
				popup.open()
				self.start_new_game()				
				
			else:
   
				for b in self.bots:
					round_res += f"Bot {b.id}'s health: {b.health}\n\n"				
		
					
				show_fading_alert(f'Round {self.current_round} is over', round_res, duration=.6, fade_duration=0.5)

			return

		title_label = self.find_id_in_parents("header_label")

		if title_label is not None:	
			title_label.text = f"Game {self.games_started}.   Round {self.current_round}.  Turn {self.current_turn + 1}."
   
		self.history_manager.start_turn(self)

		for b in self.shuffled_bots:
			b.ready_for_next_turn = False  
			b.submit_prompt_to_llm()
		
		

	def on_bot_llm_interaction_complete(self, bot):
		"""Callback when a bot's LLM interaction is complete."""
		bot.ready_for_next_turn = True
  		
		if all(b.ready_for_next_turn for b in self.bots):      
			self.current_turn += 1
			self.history_manager.end_turn(self)
			Clock.schedule_once(self.play_turn, 0)
			
			
      				


	def get_bot_by_id(self, id):
		"""Returns the bot instance with the specified ID."""
		for bot_instance in self.bots:
			if bot_instance.id == id:
				return bot_instance
		return None




	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		"""Handles keyboard input for bot commands."""	

		if modifiers and 'shift' in modifiers:
			bot_id = 2
		else:
			bot_id = 1

		bot = self.get_bot_by_id(bot_id)


		if keycode[1] == 'escape':            
				keyboard.release()

		else:
			match keycode[1]:
				
				case 'm':
					bot.move()
				  
				case 'r':
					bot.rotate(.2)

				case 't':
					bot.rotate(-.2)
				  
				case 's':
					bot.toggle_shield()

				case 'spacebar':           
					# TODO move bot sounds inside the bot class
					if not bot.shield:
						Clock.schedule_once(lambda dt: self.snd_shoot.play())

					bullet = bot.shoot()                    						

					self.bullet_alpha = 1

					alive = True                    
					damaged_bot_id = None

					if bullet is None:
						alive = False

					while alive:
						(alive, damaged_bot_id) = bullet.update(self.bots)

						# only draw bulltes outside the shooting bot                        
						dist = ((bullet.x - bot.x) ** 2 + (bullet.y - bot.y) ** 2) ** 0.5
						if dist *.97 > bot.diameter / 2:
							self.bulletTrace.append((bullet.x, bullet.y))
					
					if damaged_bot_id is not None:						
						Clock.schedule_once(lambda dt: self.snd_hit.play())						
						self.get_bot_by_id(damaged_bot_id).damage()
						
					else:
						pass
												   
			
			return True