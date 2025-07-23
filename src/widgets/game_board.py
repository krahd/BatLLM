from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, Translate, Rotate, PushMatrix, PopMatrix
from bot import Bot
from normalized_canvas import NormalizedCanvas
from kivy.core.window import Window
from kivy.clock import Clock


class GameBoardWidget(Widget):
    
    bots = []
    bulletTrace = []
    bullet_alpha = 1

    def __init__(self, **kwargs):
        super(GameBoardWidget, self).__init__(**kwargs)
        
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down = self._on_keyboard_down)
        
        self.bind(size=self._redraw, pos=self._redraw)

        self.bulletTrace = []  # Initialize bullet trace list
        self.bullet_alpha = 1  # Initialize bullet alpha value

        Clock.schedule_interval(self._redraw, 1.0 / 10.0)  # Schedule redraw at 60 FPS  



    def add_bots(self, bots):
        """Adds a list of bots to the game board."""
        self.bots = bots



            
    def on_kv_post(self, base_widget):
        """This method is called after the KV rules have been applied."""
        super().on_kv_post(base_widget)
        self.bots = [Bot(id=i, board_widget=self) for i in range(1, 3)]
        



    def _keyboard_closed(self): # virtual keyboard closed handler
        print('keyboard have been closed!')
        self._keyboard.unbind(on_key_down = self._on_keyboard_down)
        self._keyboard = None




    def _redraw(self, *args):
        self.render()



            
    def render(self, *args):      
        """Renders the game board and all bots."""              
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
               

        
            
                        
    # mouse button down event handler    
    def on_touch_down(self, touch):
        """Handles mouse click events on the game board."""
        if self.collide_point(touch.x, touch.y):         
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
            
            for bot in self.bots:
                print ("-- " , bot.x)
            
            return True   
                
        return super().on_touch_down(touch)  



    # mouse drag event handler
    def on_touch_move(self, touch):
        """Handles mouse drag events on the game board."""
        if self.collide_point(touch.x, touch.y):
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
           
            return True
        
        return super().on_touch_move(touch)



    def find_id_in_parents(self, target_id):
        parent = self.parent
        while parent:
            if hasattr(parent, 'ids') and target_id in parent.ids:
                return parent.ids[target_id]
            parent = parent.parent
        return None




    def add_command_to_history(self, bot_id, command):
        """Adds a command to the output history box for the specified bot."""            
        if bot_id == 1:
            box = self.find_id_in_parents("output_history_player_1")
        elif bot_id == 2:
            box = self.find_id_in_parents("output_history_player_2")
        else:
            print(f"Invalid bot_id: {bot_id}")
            return

        if box is not None:
            box.text += f"{len(box.text.splitlines()) + 1}. {command}\n"
        else:
            print(f"Could not find output history box for bot_id: {bot_id}")

 

 
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handles keyboard input for bot commands."""
    

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

                case 'spacebar':                    
                    bullet = bot.shoot()
                    self.bullet_alpha = 1
                    alive = True                    
                    damaged_bot_id = None

                    if bullet is None:
                        alive = False

                    while alive:

                        (alive, damaged_bot_id) = bullet.update(self.bots)
                        self.bulletTrace.append((bullet.x, bullet.y))
                        
                    
                    if damaged_bot_id is not None:
                        print(f"Bot {damaged_bot_id} was hit by a bullet from Bot {bot.id}!")
                        self.get_bot_by_id(damaged_bot_id)
                        self.get_bot_by_id(damaged_bot_id).damage()
                        
                    else:
                        print(f"Bullet from Bot {bot.id} did not hit any bot.")
                                                   
            
            return True

        

    #TODO move this to a separate file and import it, do the same in home_screen.py
    #TODO create a class Bots that holds all bots and this kind of methods
    def get_bot_by_id(self, id):
        """Returns the bot instance with the specified ID."""
        for bot_instance in self.bots:
            if bot_instance.id == id:
                return bot_instance
        return None