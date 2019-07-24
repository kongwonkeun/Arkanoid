#
#
#

import enum
import pygame

from arkanoid.utils.util import load_png
from arkanoid.utils.util import load_png_sequence

class Brick(pygame.sprite.Sprite):

    def __init__(self, brick_colour, round_no, powerup_cls = None):
        super().__init__()
        self.colour = brick_colour
        self.image, self.rect = load_png('brick_{}'.format(brick_colour.name))
        self._image_sequence = [image for image, _ in load_png_sequence('brick_{}'.format(brick_colour.name))]
        self._animation = None
        self.collision_count = 0
        self.powerup_cls = powerup_cls
        if  brick_colour == BrickColour.silver:
            self.value = brick_colour.value * round_no
        else:
            self.value = brick_colour.value
        if  brick_colour == BrickColour.silver:
            self._destroy_after = 3
        elif brick_colour == BrickColour.gold: #---- kong ----
            self._destroy_after = -1
        else:
            self._destroy_after = 1

    def update(self):
        if self._animation:
            try:
                self.image = next(self._animation)
            except StopIteration:
                self._animation = None

    @property
    def visible(self):
        if  self._destroy_after > 0:
            return self.collision_count < self._destroy_after
        return True

    def animate(self):
        self._animation = iter(self._image_sequence)

class BrickColour(enum.Enum):
    blue = 100
    cyan = 70
    gold = 0 #---- kong ----
    green = 80
    orange = 60
    pink = 110
    red = 90
    silver = 50
    white = 40
    yellow = 120

#
#
# 