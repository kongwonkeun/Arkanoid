#
#
#

import collections
import pygame

from arkanoid.sprites.edge import (TopEdge, SideEdge)
from arkanoid.sprites.brick import BrickColour

# background colours
BLUE = (0, 0, 128)
GREEN = (0, 128, 0)
RED = (128, 0, 0)

class BaseRound:

    def __init__(self, top_offset):
        self.top_offset = top_offset
        self.screen = pygame.display.get_surface()
        self.name = 'Roune Name'
        self.edges = self._create_edges()
        self.background = self._create_background()
        self.screen.blit(self.background, (0, top_offset))
        self.bricks = self._create_bricks()
        self.ball_base_speed_adjust = 0
        self.paddle_speed_adjust = 0
        self.ball_speed_normalisation_rate_adjust = 0
        self.enemy_type = None
        self.num_enemies = 0
        self.next_round = None
        self._bricks_destroyed = 0

    @property
    def complete(self):
        return self._bricks_destroyed >= len([brick for brick in self.bricks if brick.colour != BrickColour.gold]) #---- kong ----

    def brick_destroyed(self):
        self._bricks_destroyed += 1

    def can_release_enemies(self):
        raise NotImplementedError('subclasses must implement can_release_enemies()')

    def _blit_brick(self, brick, x, y):
        offset_x = brick.rect.width * x
        offset_y = brick.rect.height * y
        rect = self.screen.blit(
            brick.image, 
            (self.edges.left.rect.x + self.edges.left.rect.width + offset_x, self.edges.top.rect.y + self.edges.top.rect.height + offset_y)
        )
        brick.rect = rect
        return brick

    def _create_background(self):
        background = pygame.Surface(self.screen.get_size())
        background = background.convert()
        background.fill(self._get_background_colour())
        return background

    def _get_background_colour(self):
        raise NotImplementedError('subclasses must implement _get_background_colour()')

    def _create_edges(self):
        edges = collections.namedtuple('edge', 'left right top')
        left_edge = SideEdge('left')
        right_edge = SideEdge('right')
        top_edge = TopEdge()
        left_edge.rect.topleft = 0, self.top_offset
        right_edge.rect.topright = self.screen.get_width(), self.top_offset
        top_edge.rect.topleft = left_edge.rect.width, self.top_offset
        return edges(left_edge, right_edge, top_edge)

    def _create_bricks(self):
        raise NotImplementedError('subclasses must implement _create_bricks()')

#
#
#
