#
#
#

import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round4 import Round4
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp, ExtraLifePowerUp, LaserPowerUp)

class Round3(BaseRound):

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 3'
        self.next_round = Round4
        self.enemy_type = EnemyType.molecule
        self.num_enemies = 3
        self.ball_base_speed_adjust = -2
        self.paddle_speed_adjust = -2
        self.ball_speed_normalisation_rate_adjust = 0.05

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_bricks(self):
        rows = []
        rows += [BrickColour.green] * 13 # row 1
        rows += [BrickColour.white] * 3  # row 2
        rows += [BrickColour.gold] * 10
        rows += [BrickColour.red] * 5    # row 3
        rows += [(BrickColour.red, DuplicatePowerUp)]
        rows += [BrickColour.red] * 7
        rows += [BrickColour.gold] * 10  # row 4
        rows += [BrickColour.white] * 3
        rows += [BrickColour.pink] * 4   # row 5
        rows += [(BrickColour.pink, DuplicatePowerUp)]
        rows += [BrickColour.pink] * 3
        rows += [(BrickColour.pink, ExtraLifePowerUp)]
        rows += [BrickColour.pink] * 4
        rows += [BrickColour.blue] * 3   # row 6
        rows += [BrickColour.gold] * 10
        rows += [BrickColour.cyan] * 2   # row 7
        #rows += [(BrickColour.cyan,  CatchPowerUp)]
        rows += [(BrickColour.cyan,  LaserPowerUp)]
        rows += [BrickColour.cyan] * 3
        rows += [(BrickColour.cyan,  ExtraLifePowerUp)]
        rows += [BrickColour.cyan] * 6
        rows += [BrickColour.gold] * 10  # row 8
        #rows += [(BrickColour.cyan,  CatchPowerUp)]
        rows += [(BrickColour.cyan,  LaserPowerUp)]
        rows += [BrickColour.cyan] * 2

        bricks = []
        x, y = 0, self._TOP_ROW_START

        for i, row in enumerate(rows):
            if  i and i % 13 == 0:
                y += 2
                x = 0
            try:
                colour, powerup = row
            except TypeError:
                colour, powerup = row, None
            brick = Brick(colour, 3, powerup_cls = powerup)
            bricks.append(self._blit_brick(brick, x, y))
            x += 1
        return pygame.sprite.Group(*bricks)

#
#
#
