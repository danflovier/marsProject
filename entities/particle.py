import random

from entities.drawable_entity import DrawableEntity
from utils import rect_in_world, rects_are_overlapping


class Particle(DrawableEntity):
    SIZE = 5
    COLOR = 'green'

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, canvas):
        top_left, bottom_right = self.get_bounds()
        canvas.create_oval(top_left.x,
                           top_left.y,
                           bottom_right.x,
                           bottom_right.y,
                           fill=self.COLOR,
                           outline="")


    @staticmethod
    def generate_particle(x,y):
        particle = Particle(x, y)
        return particle
