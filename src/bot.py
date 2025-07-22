from math import cos, sin
from kivy.graphics import Color, Rectangle, Ellipse, Line, Translate, Rotate, PushMatrix, PopMatrix, Scale
import math
import random
from kivy.core.text import Label as CoreLabel
from kivy.uix.widget import Widget
from normalized_canvas import NormalizedCanvas


class Bot:
    id = None
    prompt_history = None
    prompt_history_index = None
    prompt_submitted = None
    
    llm_endpoint = None
    
    x = None
    y = None
    rot = None # in radians
    shield = None
    shield_range = None
    health = None
    step = None

    diameter = None
    colour = None
    

            
    def render(self, canvas):
        r = self.diameter / 2
        d = self.diameter

        with canvas:

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
            Line (points=(0, 0, d / 1.8, 0), width=0.002)

            # shield
            if self.shield:
                Color(0, .5, 1, 1)            
                Line (ellipse = (-r, -r, d, d, 90 - self.shield_range, 90 + self.shield_range), width=0.0050) # TODO check 90-
            
            PopMatrix()

            # info box
            PushMatrix()
            Translate(self.x, self.y)
            
            Color (0, 0, 0, .2)
            Line(rectangle=(r, r, .2, .2), width=0.001)
            
            Color (1, 1, 1, .6)
            Rectangle(pos=(r, r), size=(.2, .2))

            Color (0, 0, 0, 1)
        
            PopMatrix()

            #TODO FIX: can't draw text at all!
        with canvas:
            mylabel = CoreLabel(text = "Hi there!", font_size = 25, color = (0, 0, 0, 1))
            # Force refresh to compute things and generate the texture
            mylabel.refresh()
            # Get the texture and the texture size
            texture = mylabel.texture
            texture_size = list(texture.size)
            # Draw the texture on any widget canvas
            myWidget = Widget()
            myWidget.canvas.add(Rectangle(texture = texture, size = texture_size))

            

    
    def __init__(self, id):
        self.diameter = 0.1 # TODO get from config
                
        self.id = id
        self.prompt_history = [] 
        self.prompt_history_index = 0
        
        if id == 1:
            self.colour = (.8, .88, 1, .85) # TODO get from config
            self.llm_endpoint = "http://localhost:5000" # TODO get from config
        else:
            self.colour = (.8, 65, .9, .85) # TODO get from config
            self.llm_endpoint = "http://localhost:5000" # TODO get from config
     

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
    def rotate(self, angle=0.1):
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
                
        self.prompt_history[self.prompt_history_index]
        

        
    def get_prompt(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        return res



    def submit_prompt_to_llm(self):
         return "M"


