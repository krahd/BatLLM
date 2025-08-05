from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale

class NormalizedCanvas:
    """A context manager that unifies coordinate systems for Kivy widgets. 
    It normalizes the coordinates to a range of 0 to 1, making it easier to work with different widget sizes and positions.
    It is used to draw on the canvas of a widget, allowing for consistent rendering across different screen sizes and resolutions.
    It also handles padding and scaling to ensure that the drawing area is consistent regardless of the widget's size.
    Top-left corner of the widget is (0, 0) and bottom-right corner is (1, 1).
    It can be used in a `with` statement to automatically handle the canvas transformations.
    """
    
    def __init__(self, widget):
        """Initializes the NormalizedCanvas with a widget.
        Args:
            widget (_type_): The Kivy widget whose canvas will be normalized.
        """
        self.widget = widget
        self.canvas = widget.canvas

    def __enter__(self):        
        """Enters the context manager, setting up the canvas transformations.
        This is called when the `with` block is entered, ensuring that the canvas is prepared for drawing.
        It applies translations and scaling to normalize the coordinates to the widget's dimensions.
        Returns:
            _type_: The canvas context, allowing for drawing operations within the `with` block.
        """

        
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
        
        # Scale to the smaller of inner_width and inner_height to keep the board square
        scale_size = min(inner_width, inner_height)              
    
        Scale(scale_size, -scale_size, 1)
        Scale (.95, .95, 1)
        Translate(0.17, .03, 0)
        #Translate(offset_x, offset_y, 0)
        
        
        return self._canvas_context 

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exits the context manager, restoring the canvas state.
        This is called when the `with` block is exited, ensuring that the canvas transformations are cleaned up.
        """
        PopMatrix()      
        self.canvas.__exit__(exc_type, exc_val, exc_tb)



    @staticmethod
    def to(widget, x, y):   
        """Converts absolute coordinates (x, y) to normalized coordinates within the widget.
        The coordinates are normalized to the range [0, 1] based on the widget's size.
        Args:
            widget (_type_): The Kivy widget to which the coordinates are relative.
            x (float): The x-coordinate to normalize.       
            y (float): The y-coordinate to normalize.
        Returns:
            tuple: A tuple containing the normalized x and y coordinates.   
        """     
        if widget.width == 0 or widget.height == 0:
            return 0.0, 0.0  
            
        local_x = x - widget.x
        local_y = y - widget.y
        nx = local_x / float(widget.width)
        ny = 1.0 - (local_y / float(widget.height))
        return nx, ny



    @staticmethod
    def touch_to(widget, touch):
        """Converts a touch event's coordinates to normalized coordinates within the widget.
        Args:
            widget (_type_): The Kivy widget to which the touch coordinates are relative.
            touch (_type_): The touch event containing x and y coordinates. 
        Returns:
            tuple: A tuple containing the normalized x and y coordinates of the touch event.    
        """        
        return NormalizedCanvas.normalize_point(widget, touch.x, touch.y)