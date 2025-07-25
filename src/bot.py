from math import cos, sin
from kivy.graphics import Color, Rectangle, Ellipse, Line, Translate, Rotate, PushMatrix, PopMatrix, Scale
import math
import random
from kivy.core.text import Label 
from kivy.uix.widget import Widget
from bullet import Bullet
from normalized_canvas import NormalizedCanvas
from kivy.network.urlrequest import UrlRequest
import json
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty
from app_config import config




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
    ready_for_next_round = None
    ready_for_next_turn = None
    agmenting_prompt = None
    
    llm_endpoint = None
    shield_range = None
    step = None
    diameter = None
    colour = None

    session_history = ObjectProperty(None)  # Reference to the history widget, if needed
        

    def __init__(self, id, board_widget, **kwargs):
        super().__init__(**kwargs)
        
        self.id = id
        self.prompt_history = [] 
        self.prompt_history_index = 0
        self.board_widget = board_widget
        self.ready_for_next_round = False
        self.ready_for_next_turn = False
        self.agmenting_prompt = config.get("game", "prompt_augmentation")        
        
        if id == 1:
            self.colour = (.8, .88, 1, .85)                        
        elif id:
            self.colour = (.8, 65, .9, .85) 
        else:
            self.colour = (0, 1, 0, 1)

        port_base = config.get("llm", "port_base")
        if not config.get("game", "independet_models"):
            port = f"{port_base + 1}"  # shared model for both bots in 5000. It could be a third one. 
            #TODO consider adding the functionality to the home screen to restart the LLMs
        else:            
            port = f"{port_base + id}"  # ports 5001, 5002, etc. for each bot
            
        self.llm_endpoint = config.get("llm", "url") + ":" + port + config.get("llm", "path")
        
        self.diameter = config.get("game", "bot_diameter")  
        self.shield = config.get("game", "shield_initial_state") 
        self.shield_range = config.get("game", "shield_size") 
        self.health = config.get("game", "initial_health")
        self.step = config.get("game", "step_length") 

        # Randomly initialize position and rotation of each bot
        self.x = random.uniform(0, 1) 
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 2 * math.pi)   
        
        self.session_history = []


    def render(self):
        r = self.diameter / 2
        d = self.diameter

        PushMatrix()
        Translate(self.x, self.y)
        
        Rotate(math.degrees(self.rot), 0, 0, 1)

        Color(*self.colour) # fill
        Ellipse(pos=(-r, -r), size=(d, d))

        Color(0, 0, 0, .7) # outline
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
    def append_prompt_to_history(self, new_prompt):
        self.prompt_history.append(new_prompt)
        self.prompt_history_index = len(self.prompt_history) - 1        
        self.ready_for_next_round = True

        
    def rewind_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index > 0:
            self.prompt_history_index -= 1            
            # print(f"Rewound to prompt: {self.prompt_history_index}")



    def forward_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index < len(self.prompt_history) - 1:
            self.prompt_history_index += 1                        
            # print(f"Forwarded to prompt: {self.prompt_history_index}")




    def get_current_prompt_from_history(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        
        return res

    def get_current_prompt(self):
        """Returns the current prompt."""
        return self.get_current_prompt_from_history()    

    def get_prompt(self):
        return self.get_current_prompt_from_history()
    
    

    def augmenting_prompt(self, augmenting):
        """Controls whether the prompt is augmented with additional information."""
        self.agmenting_prompt = augmenting
                

    def prepare_prompt_submission(self, new_prompt):
        """Gets ready to execute"""
        self.append_prompt_to_history(new_prompt)        
                


    def submit_prompt_to_llm(self):    
        
        headers = {"Content-Type": "application/json"}
        
        data = {
            "model": "llama3.2:latest",
            "prompt": "",
            "stream": False
        }

        # if so chosen we augment the prompt, kind of a RAG
        if config.get("game", "prompt_augmentation"): 

            # we reload the prompt_augmentation_header in case it has changed
            file = open(config.get("llm", "augmentation_header_file"),'r')
            hdr = file.read()
            file.close()
            data["prompt"] = hdr           
            data["prompt"] += f"Self.x: {self.x}, Self.y: {self.y}\n"
            data["prompt"] += f"Self.rot: {math.degrees(self.rot)}\n"
            data["prompt"] += f"Self.shield: {'ON' if self.shield else 'OFF'}\n"
            data["prompt"] += f"Self.health: {self.health}\n"
            data["prompt"] += f"Opponent.x: {self.board_widget.get_bot_by_id(3 - self.id).x}, Opponent.y: {self.board_widget.get_bot_by_id(3 - self.id).y}\n"
            data["prompt"] += f"Opponent.rot: {math.degrees(self.board_widget.get_bot_by_id(3 - self.id).rot)}\n"
            data["prompt"] += f"Opponent.shield: {'ON' if self.board_widget.get_bot_by_id(3 - self.id).shield else 'OFF'}\n"
            data["prompt"] += f"Opponent.health: {self.board_widget.get_bot_by_id(3 - self.id).health}\n"
            data["prompt"] += "User prompt:"
            
        data["prompt"] += self.get_current_prompt() + "\n"
        
        # print(f"[{self.id}] Sending prompt to LLM: {data['prompt']}")
        # TODO format these prints better and output them into to a log window that can be opened and closed by the user instead of the console
        print(f"[{self.id}] Sending the prompt to the LLM")
        
        UrlRequest(
            url = self.llm_endpoint,
            req_body = json.dumps(data), 
            req_headers = headers, #TODO move to a global variable
            on_success = self._on_llm_response,
            on_failure = self._on_llm_failure,   # HTTP errors 4xx, 5xx
            on_error = self._on_llm_error,     # other errors (no connection, etc.)
            timeout = 30,
            method = 'POST'
        )
        


    def _on_llm_failure(self, request, error):
        """Callback for HTTP failures."""
        print(f"[{self.id}] LLM request failed: {error}")                
        self.board_widget.on_bot_llm_interaction_complete(self) 


        
    def _on_llm_error(self, request, error):
        """Callback for errors or HTTP failures."""
        print(f"[{self.id}] Error during LLM request: {error}")                 
        self.board_widget.on_bot_llm_interaction_complete(self)  
                
                 
    def _on_llm_response(self, req, result):        
        print (f"[{self.id}] LLM response received: {result.get('response', '')}")  
                   
        cmd = result.get("response", "").strip()
        # print ("Bot ", self.id, " response: ", cmd)  # Debugging output 
            
        # ********* Processing the response *********
        command_ok = True
        try: 
            if isinstance(cmd, str):
                command = cmd
            elif isinstance(cmd, list) and len(cmd) > 0:
                command = cmd[0]
            else:
                command_ok = False
                
            if command_ok:
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
                        return self.shoot() 
                        
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
                    case _:
                        command_ok = False
     
        except Exception as e:
            command_ok = False
            print (f"exception: {e}") 
        
        if not command_ok:
            #TODO play a subtle sound if command_ok is False?
            print(f"[{self.id}] Invalid command: {command}")
            self.board_widget.add_llm_response_to_history(self.id, "ERR")
        else:
            print(f"[{self.id}] Command OK: {command}")
            self.board_widget.add_llm_response_to_history(self.id, command)        

        # ********* Updating the bot's state and notifying the board widget *********
        self.ready_for_next_turn = True
        self.board_widget.on_bot_llm_interaction_complete(self)  



    def damage(self):
        """Damages the bot, reducing its health."""
        self.health -= config.get("game", "bullet_damage")
        
        if self.health < 0:
            self.health = 0
            print(f"Bot {self.id} has been destroyed!")


    def toggle_shield(self):
        """Toggles the shield state."""
        self.shield = not self.shield


    def shoot(self):
        """Shoots a projectile from the bot."""
        if not self.shield:            
            bullet = Bullet(self.id, self.x, self.y, self.rot)            
            return bullet
        else:            
            return None
        