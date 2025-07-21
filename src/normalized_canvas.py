from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale

class NormalizedCanvas:
    """Context manager for normalized (0 to 1) coordinate drawing in a Kivy widget."""
    def __init__(self, widget):
        self.widget = widget
        self.canvas = widget.canvas

    def __enter__(self):        
        self._canvas_context = self.canvas.__enter__()
        
        PushMatrix()
        Translate(self.widget.x, self.widget.y + self.widget.height, 0)      

        padding = getattr(self.widget, "padding", [0, 0, 0, 0])
        if isinstance(padding, (int, float)):
            padding = [padding] * 4
        elif isinstance(padding, tuple):
            padding = list(padding)
        if len(padding) == 2:
            padding = [padding[0], padding[1], padding[0], padding[1]]
        elif len(padding) == 1:
            padding = [padding[0]] * 4

        pad_left, pad_top, pad_right, pad_bottom = padding

        inner_width = self.widget.width - pad_left - pad_right
        inner_height = self.widget.height - pad_top - pad_bottom
       
        #Scale(self.widget.width, -self.widget.height, 1)
        

        # Scale(inner_width, -inner_height, 1)           # TODO calculate scale and position based on widget size
        Scale(inner_height, -inner_height, 1)          
        Scale (.95, .95, 1)
        Translate(0.17, .03, 0)
        
        
        return self._canvas_context 

    def __exit__(self, exc_type, exc_val, exc_tb):      
        PopMatrix()      
        self.canvas.__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def to(widget, x, y):        
        if widget.width == 0 or widget.height == 0:
            return 0.0, 0.0  
   
        local_x = x - widget.x
        local_y = y - widget.y
        nx = local_x / float(widget.width)
        ny = 1.0 - (local_y / float(widget.height))
        return nx, ny

    @staticmethod
    def touch_to(widget, touch):        
        return NormalizedCanvas.normalize_point(widget, touch.x, touch.y)