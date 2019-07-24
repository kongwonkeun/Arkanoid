#
#
#

import operator
import random
import pygame

from arkanoid.utils.util import (load_png, load_png_sequence)

DOOR_TOP_LEFT = 'door_top_left'
DOOR_TOP_RIGHT = 'door_top_right'
DOOR_OPEN_DELAY_MIN = 60  # frames
DOOR_OPEN_DELAY_MAX = 600 # frames
DOOR_OPEN_TIME = 20 # frames
COORDS = {
    DOOR_TOP_LEFT:  (115, 150),
    DOOR_TOP_RIGHT: (415, 150)
}

class TopEdge(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.image, self.rect = load_png('edge_top')
        self._image_sequence = {
            DOOR_TOP_LEFT:  load_png_sequence(DOOR_TOP_LEFT),
            DOOR_TOP_RIGHT: load_png_sequence(DOOR_TOP_RIGHT)
        }
        self._door_open_animation = None
        self._door_close_animation = None
        self._open_queue = []
        self._open_until = 0
        self._update_count = 0
        self.visible = True

    def update(self):
        if  not self._door_open_animation and not self._door_close_animation:
            if  self._open_queue:
                delay, door, _ = self._open_queue[0]
                if  self._update_count >= delay:
                    self._door_open_animation = iter(self._image_sequence[door])
        if  self._door_open_animation:
            self._animate_open_door()
        elif (self._door_close_animation and self._update_count > self._open_until):
            self._animate_close_door()
        self._update_count += 1

    def _animate_open_door(self):
        if  self._update_count % 4 == 0:
            try:
                self.image, _ = next(self._door_open_animation)
            except StopIteration:
                _, door, on_open = self._open_queue.pop(0)
                self._door_close_animation = iter(reversed(self._image_sequence[door]))
                self._door_open_animation = None
                self._open_until = self._update_count + DOOR_OPEN_TIME
                on_open()

    def _animate_close_door(self):
        if  self._update_count % 4 == 0:
            try:
                self.image, _ = next(self._door_close_animation)
            except StopIteration:
                self._door_close_animation = None

    def open_door(self, on_open):
        door  = random.choice((DOOR_TOP_LEFT, DOOR_TOP_RIGHT))
        delay = random.choice(range(DOOR_OPEN_DELAY_MIN, DOOR_OPEN_DELAY_MAX))
        delay += self._update_count
        self._open_queue.append((delay, door, lambda: on_open(COORDS[door])))
        self._open_queue.sort(key=operator.itemgetter(0))

    def cancel_open_door(self):
        self._open_queue.clear()
        self._door_open_animation = None
        self._door_close_animation = None
        self.image, _ = load_png('edge_top')

class SideEdge(pygame.sprite.Sprite):
    def __init__(self, side):
        if  side not in ('left', 'right'):
            raise AttributeError("side must be either 'left' or 'right'")
        super().__init__()
        self.image, self.rect = load_png('edge_%s' % side)
        self.visible = True

    def update(self):
        pass

#
#
#
