#
#
#

import random
import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round2 import Round2
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, ExpandPowerUp, ExtraLifePowerUp, LaserPowerUp, SlowBallPowerUp)

class Round1(BaseRound):

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 1'
        self.next_round = Round2
        self.enemy_type = EnemyType.cone
        self.num_enemies = 3

    def can_release_enemies(self):
        return self._bricks_destroyed >= len(self.bricks) // 4

    def _get_background_colour(self):
        return BLUE

    def _create_bricks(self):
        colours = (BrickColour.silver, BrickColour.red, BrickColour.yellow, BrickColour.blue, BrickColour.green)
        powerup_classes = []
        powerup_classes.extend([CatchPowerUp] * 3)
        powerup_classes.extend([ExpandPowerUp] * 4)
        powerup_classes.extend([ExtraLifePowerUp] * 3)
        powerup_classes.extend([SlowBallPowerUp] * 2)
        powerup_classes.extend([LaserPowerUp] * 4)
        random.shuffle(powerup_classes)

        powerup_indexes = random.sample(range(52), len(powerup_classes) - 4)
        powerup_indexes += random.sample(range(52, 65), 4)
        powerup_indexes.sort()

        bricks, count = [], 0

        for colour in colours:
            for _ in range(13):
                powerup_class = None
                if  count in powerup_indexes:
                    powerup_class = powerup_classes.pop(0)
                brick = Brick(colour, 1, powerup_cls = powerup_class)
                bricks.append(brick)
                count += 1
        self._position_bricks(bricks)
        return pygame.sprite.Group(*bricks)

    def _position_bricks(self, bricks):
        x, y, last_colour = 0, 3, None
        for brick in bricks:
            if  brick.colour != last_colour:
                last_colour = brick.colour
                x = 0
                y += 1
            else:
                x += 1
            self._blit_brick(brick, x, y)

#
#
#
