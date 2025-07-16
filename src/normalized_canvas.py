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
        Scale(self.widget.width, -self.widget.height, 1)          
        return self._canvas_context 

    def __exit__(self, exc_type, exc_val, exc_tb):      
        PopMatrix()      
        self.canvas.__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def to(widget, x, y):        
        if widget.width == 0 or widget.height == 0:
            return 0.0, 0.0  # Avoid division by zero for degenerate widget size
   
        local_x = x - widget.x
        local_y = y - widget.y
        nx = local_x / float(widget.width)
        ny = 1.0 - (local_y / float(widget.height))
        return nx, ny

    @staticmethod
    def touch_to(widget, touch):        
        return NormalizedCanvas.normalize_point(widget, touch.x, touch.y)