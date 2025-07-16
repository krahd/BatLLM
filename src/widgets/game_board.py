
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from normalized_canvas import NormalizedCanvas

class GameBoardWidget(Widget):
    ps = [] 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._redraw, pos=self._redraw)
        self.ps = []  
        

    def _redraw(self, *args):
        self.render()
            
    def render(self, *args):        
        self.canvas.clear()
        
        with NormalizedCanvas(self):
            Color(1, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(1, 1))  

            Color(0, 1, 0, 1)  
            for x, y in self.ps:                               
                Rectangle(pos=(x, y), size=(0.01, 0.01))
            
            
        
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
           