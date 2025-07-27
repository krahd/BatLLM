import random

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget

from kivy.uix.label import Label
from kivy.uix.popup import Popup

from util.normalized_canvas import NormalizedCanvas
import os

from configs.app_config import config
from game.bot import Bot
from game.history_manager import HistoryManager
from util.util import show_fading_alert, find_id_in_parents



class GameBoard(Widget):
	"""The GameBoard is BatLLM's game world. It is algo a Kivi Widget, so it can be used in the Kivy UI.
    It takes care of all the in-game logic, interacts with the bots and the history_manager.
    The HomeScreen is BatLLM with the outside world and GameBoard is the inside world implementation of everything in the game (with the exception of the LLMs, which are contacted directly by the bots).

	Args:
		Widget (_type_): Kivi's base Widget
	
	"""    

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
		"""Constructor
		"""     
		super(GameBoard, self).__init__(**kwargs)
		
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
		"""Starts a new game. It resets all the information pertaining to the previous game.
		"""     
		# reset values
		self.current_turn = None
		self.current_round = None		
		self.shuffled_bots = None
  				

     
     	# Create two bot instances with reference to this GameBoard
		self.bots = [Bot(id = i, board_widget = self) for i in range(1, 3)]

		if self.games_started > 0:
			for b in self.bots:
				self.add_text_to_llm_response_history(b.id, "[b][color=#ffa0a0]\n\nNew Game\n\n[/color][/b]")
				b.ready_for_next_round = False  # need a new prompt for a new round

		self.games_started += 1
		self.history_manager.start_game(self)
		self.update_title_label()
		


	def save_session(self, filename):
		"""Upon user confirmation it asks the HistoryManager to save all the session information recorded until this moment.

		Args:
			filename (_type_): the name of the json file.
		"""     
		folder = f"{config.get("data", "saved_sessions_folder")}"		
		os.makedirs(folder, exist_ok=True)

		filepath = os.path.join(folder, filename)
		print ("saving session to", filepath)
		self.history_manager.save_session(filepath)
		print ("done")

		print (self.history_manager.to_text()) # TODO After designing a new a screen to display the history. The screen's data will be updated here. Meanwhile the history as string is printed directly on the terminal.

   

	def on_kv_post(self, base_widget):
		"""This method is called after the KV rules have been applied

		Args:
			base_widget (_type_): The root of the tree of elements to check
		"""		
		super().on_kv_post(base_widget)

		Clock.schedule_once(lambda dt: self.start_new_game(), 0)  # Start a new game after the KV rules have been applied
		self.start_new_game() # The first game of the session is created automatically.
			


	def _keyboard_closed(self):
		"""virtual keyboard closed handler. It has no use in a desktop app.
		"""     
		print('keyboard have been closed!')
		self._keyboard.unbind(on_key_down = self._on_keyboard_down)
		self._keyboard = None



	def _redraw(self, *args):
		"""Refreshes the screen by calling render()
		"""     
		self.render()


			
	def render(self, *args):      
		"""Draws the game world in its current state.
		It uses NormalizedCanvas instead of Kivy's standard canvas to simplfy drawing.
		# TODO improve the game graphics
		"""		              
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
			   
											
	
	def on_touch_down(self, touch):
		"""Mouse click and touch event handler - it does nothing as of now.

		Args:
			touch (_type_): touch event

		Returns:
			_type_: True iff the event has been handled
		"""     
		
		if self.collide_point(touch.x, touch.y):         
			nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
			return True   
				
		return super().on_touch_down(touch)  


	
	def on_touch_move(self, touch):
		"""Mouse drag and finger drag event handler - it does nothing as of now.
		Args:
			touch (_type_): touch event

		Returns:
			_type_: True iff the event has been handled
		"""     
		
		if self.collide_point(touch.x, touch.y):
			nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)		   
			return True
		
		return super().on_touch_move(touch)
	


	def add_text_to_llm_response_history(self, bot_id, text):
		"""Adds the text to the output history box next to the bot's prompt input. 

		Args:
			bot_id (_type_): bot id
			text (_type_): text to add
		"""		
		 
		box = find_id_in_parents(self, f"output_history_player_{bot_id}")
   
		if box is not None:
			box.text += text
		else:
			print(f"Could not find output history box for bot_id: {bot_id}")



	def add_llm_response_to_history(self, bot_id, command):
		"""Adds the command parsed from the llm response to the output history next to the history widget.

		Args:
			bot_id (_type_): bot id
			command (_type_): the command to add
		"""		  
		text = f"   {self.current_turn}. {command}\n" 
		self.add_text_to_llm_response_history(bot_id, text)
        


	def submit_prompt(self, bot_id, new_prompt):
		"""Tells the bot with bot_id to start working on submitting the new_prompt to the llm
  		If all the bots have submitted a new prompt, it starts the next round.

		Args:
			bot_id (_type_): the bot id
			new_prompt (_type_): the player's prompt
		"""		
		
		bot = self.get_bot_by_id(bot_id)
		bot.prepare_prompt_submission(new_prompt)

		if all(b.ready_for_next_round for b in self.bots):
			self.play_round()



	def play_round(self):
		"""It runs recursively taking care of a complete game round
		"""     
		self.current_turn = 0
  
		if self.current_round is None:
			self.current_round = 0

		self.current_round += 1				

		for b in self.bots:
			self.add_text_to_llm_response_history(b.id, f"[b]Round {self.current_round}:[/b]\n")
			b.ready_for_next_round = False  # need a new prompt for a new round

		# shuffle bots for this coming round
		self.shuffled_bots = random.sample(self.bots, 2)

		self.history_manager.start_round(self)	
		
		self.play_turn(0)
		self.history_manager.end_turn(self)



	def game_is_over(self):
		"""Checks if the game is over.

		Returns:
			_type_: true iff the game is over (either only one bot is alive, no bot is or the max number if rounds has been met)
		"""		
	
		for b in self.bots:
			if b.health <= 0:				
				return True

		if self.current_round >= config.get("game", "total_rounds"):			
			return True

		return False

		

	def play_turn(self, dt):
		"""Executes one turn

		Args:
			dt (_type_): it is not used yet can't be deleted.
		"""     
     
		if not self.current_turn < config.get("game", "turns_per_round"):  # round's over

			self.history_manager.end_round(self)
			for b in self.bots:
				self.add_text_to_llm_response_history(b.id, "\n\n")
   
			round_res = "\n"
   
			if (self.game_is_over()):
				self.history_manager.end_game(self)				
				self.end_game()				
				self.start_new_game()				
				
			else:
				for b in self.bots:
					round_res += f"Bot {b.id}'s health: {b.health}\n\n"				
							
				show_fading_alert(f'Round {self.current_round} is over', round_res, duration=.6, fade_duration=0.5)

			return

		self.update_title_label()   
		self.history_manager.start_turn(self)
		for b in self.shuffled_bots:
			b.ready_for_next_turn = False  
			b.submit_prompt_to_llm()



	def 
  

	def end_game(self):
		"""Ends the game and displays the final results.
		"""     
		round_res = "Final Results:\n\n"
		for b in self.bots:
			round_res += f"        Bot {b.id}'s health: {b.health}\n"

		popup = Popup(title='Game Over', content=Label(text = round_res), size_hint = (None, None), size = (470, 460))
		popup.open()

		# TODO Check if there is any manintenance to do after the game is over and before starting a new one.


	def update_title_label(self):
		"""Updates the label above the game board with the current game, round and turn information.
		"""		
		game_title_label = find_id_in_parents(self, "game_title_label")
		if game_title_label is not None:	

			game_title_label.text = f"[size=32]Game {self.games_started}."
   
			if self.current_round is not None:
				game_title_label.text += "   "       
				game_title_label.text += f"Round {self.current_round}."
	
				if self.current_turn is not None:
					game_title_label.text += "   "
					game_title_label.text += f"Turn {self.current_turn + 1}."
     
			game_title_label.text += "[/size]"



	def on_bot_llm_interaction_complete(self, bot):
		"""Callback method executed after a prompt-response cycle has been completed by a bot 

		Args:
			bot (_type_): the bot id
		"""		
		bot.ready_for_next_turn = True
  		
		if all(b.ready_for_next_turn for b in self.bots):      
			self.current_turn += 1
			self.history_manager.end_turn(self)
			Clock.schedule_once(self.play_turn, 0)
			
			      				

	def get_bot_by_id(self, id):
		"""Returns the bot instance with the specified ID.

		Args:
			id (_type_): The bot with the id or None if not found.
  		"""
		for bot_instance in self.bots:
			if bot_instance.id == id:
				return bot_instance
		return None



	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		"""Keyboard handler for the game board. It is used for debug and testing purposes alone.
		Once the codebase is more mature it will probably be removed (commented out, actually)

		Args:
			keyboard (_type_): type of keyboard
			keycode (_type_): the code of the pressed key
			text (_type_): the symbol correspnding to the key
			modifiers (_type_): the modifiers being pressed (shift, command, etc).

		Returns:
			_type_: True # TODO check this.
		"""

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

				case 'b':    
					self.shoot(bot.id)												   			       
					
			return True
	 

	def shoot(self, bot_id):
		"""A bullet is shot by a bot.
		Args:
			bot_id (_type_): "The id of the bot that shoots."
		"""		
		bot = self.get_bot_by_id(bot_id)
		bullet = bot.shoot()                    						
		self.bullet_alpha = 1
		bullet_is_alive = True                    
		damaged_bot_id = None

		if bullet is not None:
			Clock.schedule_once(lambda dt: self.snd_shoot.play())
		else:		
			bullet_is_alive = False

		while bullet_is_alive:
			(bullet_is_alive, damaged_bot_id) = bullet.update(self.bots)

			# only draw the bullet when it is outside the bot that fires it
			dist = ((bullet.x - bot.x) ** 2 + (bullet.y - bot.y) ** 2) ** 0.5
			if dist *.97 > bot.diameter / 2:
				self.bulletTrace.append((bullet.x, bullet.y))
		
		if damaged_bot_id is not None:						
			Clock.schedule_once(lambda dt: self.snd_hit.play())						
			
			self.get_bot_by_id(damaged_bot_id).damage()

			if self.game_is_over():
				self.end_game()
				self.start_new_game()
			

						