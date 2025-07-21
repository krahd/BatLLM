
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from bot import Bot
from normalized_canvas import NormalizedCanvas

class GameBoardWidget(Widget):
    ps = [] 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._redraw, pos=self._redraw)
        self.ps = []  
        

    def _redraw(self, *args):
        self.render()

    def drawBoard(self):

        Color(0, 0, 0, .3)
        brd = 0.01
        Rectangle(pos=(brd, brd), size=(1 - 2 * brd, 1 - 2 * brd))
        
        Color (1,1,1,.99)
        brd = 0.011
        Rectangle(pos=(brd, brd), size=(1 - 2 * brd, 1 - 2 * brd))

        
        
            
    def render(self, *args):        
        self.canvas.clear()
        
        with NormalizedCanvas(self):
           Color(0, 0, 1, .05)
           Rectangle(pos=(0, 0), size=(1, 1))                 
    
           bot = Bot(1)
           bot.render()# Ensure bot is an instance of Bot
                
            
            
        
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
            self.ps.append((nx, ny))
            self.render()
            return True   
                
        return super().on_touch_down(touch)  

    def on_touch_move(self, touch):
        if self.collide_point(touch.x, touch.y):
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
            self.ps.append((nx, ny))
            self.render()
            return True
        
        return super().on_touch_move(touch)
           