from kivy.graphics import Color, Rectangle, Ellipse, Line, Translate, Rotate, PushMatrix, PopMatrix, Scale
import math


class Bullet:
    def __init__(self, x, y, rot):
        self.x = x
        self.y = y
        self.rot = rot

    def render(self):
        PushMatrix()
        Translate(self.x, self.y)
        Color(*self.colour)
        Ellipse(pos=(-self.radius / 2, -self.radius / 2), size=(self.radius, self.radius))
        PopMatrix()


    def tick(self):
        # Update bullet position or state here if needed
        pass

    