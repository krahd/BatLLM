from math import cos, sin
from kivy.graphics import Color, Rectangle, Ellipse, Line
import math
import random

class Bot:
    id = None
    prompt_history = None
    prompt_history_index = None
    prompt = None    
    llm_endpoint = None
    augment_prompts = None
    x = None
    y = None
    rot = None
    shield = None
    shield_range = None
    health = None
    step = None

    radius = None
    colour = None
    

    def render(self):
        x = self.x
        y = self.y
        r = self.radius
        rot = self.rot
        a = self.shield_range
        width = 0.0010  
        
        Color (*self.colour)
        Ellipse (pos=(x, y), size=(r, r))       
        Color (0, 0, 0, .7)
        Line (ellipse = (x, y, r, r), width=0.0010)
        Line(points = (x + r / 2, y + r / 2, x + r * cos(rot), y + r * sin(rot)), width=width)
        
        self.shield = True  # TODO get from config
        
        if self.shield:
            Color (0, .5, 1, 1)
            Line(ellipse=(x, y, r, r, 90, 180), width=0.0060)
            
            
    
    def __init__(self, id):
        self.radius = 0.1
        
        self.id = id
        self.prompt_history = [] 
        self.prompt_history_index = 0
        self.colour = (1, 0, 0, 1)
    
        self.prompt = None
        self.llm_endpoint = "http://localhost:5000" # TODO get from config
        self.augment_prompts = False  # TODO get from config
        self.x = random.random()  # Random initial position
        self.y = random.random()
        self.y = random.random()
        self.rot = .05
        
        self.shield = False
        self.shield_range = 0.3 # TODO get from config
        self.health = 100 # TODO get from config      
        self.step = 10 # TODO get from config
        
        
        

    # takes a step
    def move(self):        
        self.x += self.step * cos(self.rot)
        self.y += self.step * sin(self.rot)
        print(f"Bot moved to position: ({self.x}, {self.y})")   


    def submit_prompt(self, new_prompt):
        self.prompt_history.append(new_prompt)
        self.prompt_history_index = len(self.prompt_history) - 1
        self.prompt = new_prompt

        # TODO send the prompt to the LLM endpoint
        print ("********** Submitting prompt **********")
        print (new_prompt)
        print ("********** End of prompt **********")

        
        
    def rewind_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index > 0:
            self.prompt_history_index -= 1            
            print(f"Rewound to prompt: {self.prompt_history_index}")

    def forward_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index < len(self.prompt_history) - 1:
            self.prompt_history_index += 1                        
            print(f"Forwarded to prompt: {self.prompt_history_index}")

    def get_current_prompt_history(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        
        return res
    
    def copy_prompt_history(self):
        res = ""
        try:        
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
            
        self.prompt = res

        
    def get_prompt(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        return res