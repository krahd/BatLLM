from math import cos, sin
from kivy.graphics import Color, Rectangle, Ellipse, Line, Translate, Rotate, PushMatrix, PopMatrix, Scale
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
    

    def render2(self):
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

        
        Line(points = (x + r / 2, y + r / 2, x + r/2 + r * cos(rot), y + r / 2 + r * sin(rot)), width=width)
                
        if self.shield:
            Color (0, .5, 1, 1)            
            Line(ellipse=(x, y, r, r,  - a - math.degrees(rot), a - math.degrees(rot)), width=0.0060)
            #Line(ellipse=(x, y, r, r, math.degrees(rot) - a, math.degrees(rot) + a), width=0.0060)
            
    def render(self):
        PushMatrix()
        Translate(self.x, self.y)
        
        Rotate(math.degrees(self.rot), 0, 0, 1)
        
        Color(*self.colour)
        Ellipse(pos=(-self.radius / 2, -self.radius / 2), size=(self.radius, self.radius))
        Color(0, 0, 0, .7)
        r = self.radius
        Line (ellipse = (-r/2, -r/2, r, r), width=0.002)
        
        Line (points=(0, 0, self.radius / 2, 0), width=0.002)
        
        Color(0, .5, 1, 1)
        Line (ellipse = (-r/2, -r/2, r, r, 90-self.shield_range, 90+self.shield_range), width=0.0050)
        PopMatrix()
        

    
    def __init__(self, id):
        self.radius = 0.1
        
        self.id = id
        self.prompt_history = [] 
        self.prompt_history_index = 0
        if id == 1:
            self.colour = (.8, .88, 1, .7)
        else:
            self.colour = (.8, 65, .9, .7)
    
        self.prompt = None
        self.llm_endpoint = "http://localhost:5000" # TODO get from config
        self.augment_prompts = False  # TODO get from config

        self.x = random.uniform(0, 1)
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 2 * math.pi)
        
        
        self.shield = True # TODO get from config
        
        
        self.shield_range = 45 # TODO get from config
        self.health = 100 # TODO get from config      
        self.step = 0.02 # TODO get from config
        
        
        

    # takes a step
    def move(self):        
        self.x += self.step * cos(self.rot)
        self.y += self.step * sin(self.rot)
        print(f"Bot moved to position: ({self.x}, {self.y})")   


    # rotates the bot by a given angle
    def rotate(self, angle=0.1):
        self.rot += angle
        if self.rot > 2 * math.pi:
            self.rot -= 2 * math.pi
        elif self.rot < 0:
            self.rot += 2 * math.pi
        print(f"Bot rotated to angle: {self.rot} radians")


    # submits a prompt to the LLM endpoint
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