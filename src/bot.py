from math import cos, sin
from kivy.graphics import Color, Rectangle, Ellipse, Line, Translate, Rotate, PushMatrix, PopMatrix, Scale
import math
import random
from kivy.core.text import Label 
from kivy.uix.widget import Widget
from bullet import Bullet
from normalized_canvas import NormalizedCanvas
import requests
import json
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty



class Bot (Widget):
    id = NumericProperty(0)
    x = NumericProperty(0)
    y = NumericProperty(0)
    rot = NumericProperty(0) # in radians
    shield = ObjectProperty(None)
    health = NumericProperty(0)
    board_widget = ObjectProperty(None)

    prompt_history = None
    prompt_history_index = None
    prompt_submitted = None
    
    llm_endpoint = None
    shield_range = None
    step = None
    diameter = None
    colour = None

    

            
    def render(self):
        r = self.diameter / 2
        d = self.diameter

    

        PushMatrix()
        Translate(self.x, self.y)
        
        Rotate(math.degrees(self.rot), 0, 0, 1)

        # fill
        Color(*self.colour)
        Ellipse(pos=(-r, -r), size=(d, d))
        Color(0, 0, 0, .7)

        # border
        Line (ellipse = (-r, -r, d, d), width=0.002)

        # pointing direction
        Line (points=(0, 0, r, 0), width=0.002)

        # shield
        if self.shield:
            Color(.7, .5, 1, 1)            
            Color(.3,.3,.6,1)
            Line (ellipse = (-r, -r, d, d, 90 - self.shield_range, 90 + self.shield_range), width=0.007) # TODO find out why 90+
        
        PopMatrix()

        # info box
        PushMatrix()

        x = min (.95 - .116, self.x + 0.01)
        y = min (.97 - .101, self.y)

        sx = r
        sy = .005
        
        Translate(x, y)
        Color (0, 0, 0, .2)
        Line(rectangle=(sx, sy, .107, .116), width=0.001)
        
        Color (1, 1, 1, .6)
        Rectangle(pos=(sx, sy), size=(.107, .116))

        t = "x: {:.2f}\ny: {:.2f}\nrot: {:.2f}°\nshield: {}\nhealth: {}".format(
            self.x, self.y, math.degrees(self.rot), "ON" if self.shield else "OFF", self.health)
        
        Color (0, 0, 0, .7)
        mylabel = Label(text=t, font_size=24, color=(0, 0, 0, .7))
        mylabel.refresh()
        texture = mylabel.texture        
        Rectangle(pos=(0.064, 0.109), texture=texture, size=(.081, -.101))
        # /info box

        PopMatrix()

        


    def __init__(self, id, board_widget, **kwargs):
        super().__init__(**kwargs)
        
        self.diameter = 0.1 # TODO get from config
                
        self.id = id
        self.prompt_history = [] 
        self.prompt_history_index = 0
        self.board_widget = board_widget

        
        
        if id == 1:
            self.colour = (.8, .88, 1, .85) # TODO get from config
            port = "5001"
           
        else:
            self.colour = (.8, 65, .9, .85) # TODO get from config
            port = "5002"


        self.llm_endpoint = "http://localhost:" + port + "/api/generate"
        
        self.x = random.uniform(0, 1) 
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 2 * math.pi)        
        
        self.shield = True # TODO get from config
        self.shield_range = 45 # TODO get from config
        self.health = 100 # TODO get from config      
        self.step = 0.02 # TODO get from config

        self.prompt_submitted = False
        

    # takes a step
    def move(self):        
        self.x += self.step * cos(self.rot)
        self.y += self.step * sin(self.rot)
        # print(f"Bot moved to position: ({self.x}, {self.y})")   



    # rotates the bot by a given angle
    def rotate(self, angle):
        self.rot += angle
        if self.rot > 2 * math.pi:
            self.rot -= 2 * math.pi
        elif self.rot < 0:
            self.rot += 2 * math.pi
        # print(f"Bot rotated to angle: {self.rot} radians = {math.degrees(self.rot)} degrees")



    # adds the prompt to the history    
    def submit_prompt(self, new_prompt):
        self.prompt_history.append(new_prompt)
        self.prompt_history_index = len(self.prompt_history) - 1        
        self.prompt_submitted = True

         
            


    # called when the round ends, sets the prompt submitted flag to False
    def end_round(self):
        self.prompt_submitted = False



        
    def rewind_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index > 0:
            self.prompt_history_index -= 1            
            # print(f"Rewound to prompt: {self.prompt_history_index}")



    def forward_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index < len(self.prompt_history) - 1:
            self.prompt_history_index += 1                        
            # print(f"Forwarded to prompt: {self.prompt_history_index}")




    def get_current_prompt_history(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        
        return res



    def get_current_prompt(self):
        """Returns the current prompt."""
        return self.get_current_prompt_history()    

    
    
    def copy_prompt_history(self):
        """Copies the current prompt history to the clipboard."""                
        try:
            self.prompt_history[self.prompt_history_index]
        except Exception as e:
            print(f"Error accessing prompt history: {e}")
        

        
    def get_prompt(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        return res


    def augment_prompt(self, augment):
        """Augments the prompt with additional information if augment is True."""
        self.board_widget.augment_prompt = augment
        if augment:
            print("Prompt augmentation enabled.")
        else:
            print("Prompt augmentation disabled.")


    def execute_prompt_in_llm(self):        
        port = 5000 + self.id  # e.g., id=1 => port=5001
        url = f"http://localhost:{port}/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "llama3.2:latest",
            "prompt": self.get_current_prompt(),
            "stream": False
        }

        # if so chosen we augment the prompt, kind of a RAG
        if self.board_widget.augment_prompt: #TODO move this text to a text file
            data["prompt"] += """You are an expert gamer. Your task is to control a bot in a videogame called BatLLM, a two-player battle game where an LLM like you controls a bot. You receive information about the game state and a prompt written by the human player that guides your behaviours.

We refer to the human players as "player", to you as "llama", and to the in-game battle bot as "bot". We refer to the environment where the bots run as "world". The world holds the game state, receives commands from the llama, executes them and updates the game state. The prompt given to the llama is a combination of the game status and the prompt written by the player in charge of the bot.

The game is a two-player battle game where each player controls a bot through the llama. The player writes a prompt that guides the llama that, in turn, outputs the commands given to the player's bot. 

The game logic (main loop) is as follows:
- while both bots are alive:
    - each player enters a prompt that is given to their Ollama.
    - a starting player is chosen randomly
    - repeat ROUND_LENGTH times stopping earlier if one of the bots dies:
        - prompt each player's llama with the player's prompt. The llama's response will be the command that is given to the player's bot.

once the round is completed, the players can input new prompts that will be used in the upcoming round.

Each bot has a state. The state of a bot consists of the following variableS:
    x - the bot's x coordinate within the world.
    y - the bot's y coordinate within the world.
    a - the bot's rotation within the world.
    s - the state of the bot's shield (either up (1) or down (0)).
    h - the bot's health. Initially INITIAL_HEALTH. If h reaches 0 the bot dies.

Each turn the bots execute the command given to it entirely.

The commands that the bots understand are:
    Cd  - the bot rotates clockwise around its center for d degrees. Example: C20
    Ad  - the bot rotates anticlockwise around its center for d degrees. Example: D180
    M    - the bot moves forward a distance of STEP_LENGTH (it takes a stop forward). Example: M
    S1  - the bot raises its shield. It will remain up until explicitly lowered. Example: S1
    S0  - the bot lowers its shield. It will remain down until explicitly raised. Example: S0
    S    - the bit lowers its shield if up or rises it if down. Example: S
    B    - if the shield is low, the bot shoots a bullet forward. If the shield is up it does nothing. Example: B.

Everything else is ignored (this means that the bot does not do do anything in this turn).

When a bot shoots a bullet (B) the world runs the bullet behavior until the bullet either hits the other bot or goes out of bounds. This means that the other bot cannot move until the bullet hits it or leaves the screen.

When a bot is hit by a bullet in a place not covered by a raised shield, its energy decreases by BULLET_DAMAGE. If a bullet hits the raised shield it does not cause any damage. The shield only protects the 'front' of the bot. It will only stop bullets that hit it in its front, plus minus SHIELD_SIZE degrees.

Before each round starts, the players enter their prompts. 

Remember, your task is to receive the game state and to output a valid command, using the user's prompt as guideline."""

        data["prompt"] += "\n\n" + "World state:\n"
        data["prompt"] += f"Self.x: {self.x}, Self.y: {self.y}\n"
        data["prompt"] += f"Self.rot: {math.degrees(self.rot)}\n"
        data["prompt"] += f"Self.shield: {'ON' if self.shield else 'OFF'}\n"
        data["prompt"] += f"Self.health: {self.health}\n"
        data["prompt"] += f"Opponent.x: {self.board_widget.get_bot_by_id(3 - self.id).x}, Opponent.y: {self.board_widget.get_bot_by_id(3 - self.id).y}\n"
        data["prompt"] += f"Opponent.rot: {math.degrees(self.board_widget.get_bot_by_id(3 - self.id).rot)}\n"
        data["prompt"] += f"Opponent.shield: {'ON' if self.board_widget.get_bot_by_id(3 - self.id).shield else 'OFF'}\n"
        data["prompt"] += f"Opponent.health: {self.board_widget.get_bot_by_id(3 - self.id).health}\n"
        data["prompt"] += f"User prompt: {self.get_current_prompt()}\n"

        print("-" * 100)
        print (data["prompt"])
        print("-" * 100)



        # ********* Sending the prompt to the LLM *********
        try:
            response = requests.post(url, headers = headers, data = json.dumps(data))
            response.raise_for_status()
            result = response.json()
            cmd = result.get("response", "").strip()
            print ("Bot ", self.id, " response: ", cmd)  # Debugging output            
            
        except requests.RequestException as e:
            print(f"Error querying Ollama on port {port}: {e}")
            return None
               
        command_ok = True
        




        # ********* Processing the response *********
        try: 
            if isinstance(cmd, str):
                command = cmd
            elif isinstance(cmd, list) and len(cmd) > 0:
                command = cmd[0]
            else:
                command_ok = False
                raise ValueError(f"Unexpected command format: {cmd}")

            match command[0]:
                case "M":
                    self.move()
                                                       
                case "C":
                    angle = float(command[1:])
                    self.rotate(angle)

                case "A":
                    angle = float(command[1:])
                    self.rotate(-angle)

                case "B":                    
                    return self.shoot() # TODO handle bullet shooting from command
                    
                case "S":
                    if len(command) == 1:                        
                        self.toggle_shield()
                    else:
                        if command[1] == "1":
                            self.shield = True
                        elif command[1] == "0":
                            self.shield = False
                        else:
                            command_ok = False
                            raise ValueError(f"Invalid shield command: {command}")
     
        except Exception as e:
            command_ok = False
            print(f"bot {self.id} - wrong command: {cmd} || exception: ({e})") 

        if command_ok:
            self.board_widget.add_command_to_history(self.id, command)

        self.prompt_submitted = False # reset the prompt submitted flag after execution, when all bots have this flag in true then a round starts
        ''' # TODO fix render the board after each command 

        self.canvas.ask_update()
        self.board_widget.canvas.ask_update()
        Clock.schedule_once(lambda dt: self.board_widget.render())
        # Reset the prompt submitted flag after execution
        self.board_widget.render()
'''


    def damage(self):
        """Damages the bot, reducing its health."""
        self.health -= 10 # TODO get from config
        if self.health < 0:
            self.health = 0
            print(f"Bot {self.id} has been destroyed!")


    def toggle_shield(self):
        """Toggles the shield state."""
        self.shield = not self.shield


    def shoot(self):
        """Shoots a projectile from the bot."""
        if not self.shield:
            print(f"Bot {self.id} shoots!")
            bullet = Bullet(self.id, self.x, self.y, self.rot)            
            return bullet
        else:
            print(f"Bot {self.id} cannot shoot while shield is active.")
            return None
        