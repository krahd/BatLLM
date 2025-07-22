from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from bot import Bot
from normalized_canvas import NormalizedCanvas
from kivy.core.window import Window



class GameBoardWidget(Widget):
    
    bots = []

    
    def __init__(self, **kwargs):
        super(GameBoardWidget, self).__init__(**kwargs)
        
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down = self._on_keyboard_down)
        
        self.bind(size=self._redraw, pos=self._redraw)

    def add_bots(self, bots):
        self.bots = bots
        
            
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.bots = [Bot(id=i, board_widget=self) for i in range(1, 3)]
        



    def _keyboard_closed(self): # virtual keyboard closed handler
        print('keyboard have been closed!')
        self._keyboard.unbind(on_key_down = self._on_keyboard_down)
        self._keyboard = None



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
        
        
        print ("*")
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
           Color(0.3, 0, 0, .05)
           Rectangle(pos=(0, 0), size=(1, 1))                 

           for bot in self.bots:
                bot.render()    

        self.canvas.ask_update()
        print("[GameBoardWidget] render() called")
                        
    # mouse button down event handler    
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):         
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
            
            self.render()
            for bot in self.bots:
                print ("-- " , bot.x)
            
            return True   
                
        return super().on_touch_down(touch)  



    # mouse drag event handler
    def on_touch_move(self, touch):
        if self.collide_point(touch.x, touch.y):
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
           
            self.render()
            return True
        
        return super().on_touch_move(touch)


 
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
       
        # escape, release the keyboard
        if keycode[1] == 'escape':
            keyboard.release()

        if keycode[0] == 109:
            for bot in self.bots:
                print ("-- " , bot.x)
                bot.move()
                
            self.render()
            return True

        if keycode[1] == 'r':                
            for bot in self.bots:
                bot.rotate()
                
            self.render()
            return True


        # Return True to accept the key. Otherwise, it will be used by
        # the system.