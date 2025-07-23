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
            Line (ellipse = (-r, -r, d, d, 90 - self.shield_range, 90 + self.shield_range), width=0.007) # TODO check 90-
        
        PopMatrix()

        # info box
        PushMatrix()
        Translate(self.x, self.y)
        Color (0, 0, 0, .2)
        Line(rectangle=(r, r, .107, .116), width=0.001)
        
        Color (1, 1, 1, .6)
        Rectangle(pos=(r, r), size=(.107, .116))

        t = "x: {:.2f}\ny: {:.2f}\nrot: {:.2f}°\nshield: {}\nhealth: {}".format(
            self.x, self.y, math.degrees(self.rot), "ON" if self.shield else "OFF", self.health)
        
        Color (0, 0, 0, .7)
        mylabel = Label(text=t, font_size=24, color=(0, 0, 0, .7))
        mylabel.refresh()
        texture = mylabel.texture        
        Rectangle(pos=(0.064, 0.157), texture=texture, size=(.081, -.101))
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
        