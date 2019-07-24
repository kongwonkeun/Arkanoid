#
#
#

import itertools
import math
import pygame

from arkanoid.event import receiver
from arkanoid.sprites.paddle import (LaserState, NormalState, WideState)
from arkanoid.utils.util import load_png_sequence

DEFAULT_FALL_SPEED = 3

class PowerUp(pygame.sprite.Sprite):

    def __init__(self, game, brick, png_prefix, speed = DEFAULT_FALL_SPEED):
        super().__init__()
        self.game = game
        self._speed = speed
        self._animation = itertools.cycle(image for image, _ in load_png_sequence(png_prefix))
        self._animation_start = 0
        self.image = None
        self.rect = pygame.Rect(brick.rect.bottomleft, (brick.rect.width, brick.rect.height))
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self.visible = True

    def update(self):
        self.rect = self.rect.move(0, self._speed)
        if  self._area.contains(self.rect):
            if  self._animation_start % 4 == 0:
                self.image = next(self._animation)
            if  self.rect.colliderect(self.game.paddle.rect):
                if  self._can_activate():
                    if  self.game.active_powerup:
                        self.game.active_powerup.deactivate()
                    self._activate()
                    self.game.active_powerup = self
                self.game.sprites.remove(self)
                self.visible = False
            else:
                self._animation_start += 1
        else:
            self.game.sprites.remove(self)
            self.visible = False

    def _activate(self):
        raise NotImplementedError('subclasses must implement _activate()')

    def _can_activate(self):
        if  self.game.paddle.exploding or not self.game.paddle.visible:
            return False
        return True

    def deactivate(self):
        raise NotImplementedError('subclasses must implement deactivate()')

class ExtraLifePowerUp(PowerUp):

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_life')

    def _activate(self):
        self.game.lives += 1

    def deactivate(self):
        pass

class SlowBallPowerUp(PowerUp):
    
    _SLOW_BALL_SPEED = 6  # pixels per frame.

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_slow')
        self._orig_speed = None

    def _activate(self):
        self._orig_speed = self.game.ball.base_speed
        for ball in self.game.balls:
            ball.speed = self._SLOW_BALL_SPEED
            ball.base_speed = self._SLOW_BALL_SPEED

    def deactivate(self):
        for ball in self.game.balls:
            ball.speed = self._orig_speed
            ball.base_speed = self._orig_speed

class ExpandPowerUp(PowerUp):

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_expand')

    def _activate(self):
        self.game.paddle.transition(WideState(self.game.paddle))
        for ball in self.game.balls:
            ball.base_speed += 1

    def deactivate(self):
        self.game.paddle.transition(NormalState(self.game.paddle))
        for ball in self.game.balls:
            ball.base_speed -= 1

    def _can_activate(self):
        can_activate = super()._can_activate()
        if  can_activate:
            can_activate = not isinstance(self.game.active_powerup, self.__class__)
        return can_activate

class LaserPowerUp(PowerUp):

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_laser')

    def _activate(self):
        self.game.paddle.transition(LaserState(self.game.paddle, self.game))
        for ball in self.game.balls:
            ball.base_speed += 1

    def deactivate(self):
        self.game.paddle.transition(NormalState(self.game.paddle))
        for ball in self.game.balls:
            ball.base_speed -= 1

    def _can_activate(self):
        can_activate = super()._can_activate()
        if  can_activate:
            can_activate = not isinstance(self.game.active_powerup, self.__class__)
        return can_activate

class CatchPowerUp(PowerUp):

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_catch')

    def _activate(self):
        self.game.paddle.ball_collide_callbacks.append(self._catch)
        receiver.register_handler(pygame.KEYUP, self._release_ball)

    def deactivate(self):
        self.game.paddle.ball_collide_callbacks.remove(self._catch)
        receiver.unregister_handler(self._release_ball)
        for ball in self.game.balls:
            ball.release()

    def _release_ball(self, event):
        if  event.key == pygame.K_SPACE:
            for ball in self.game.balls:
                ball.release()

    def _catch(self, ball):
        pos = (ball.rect.bottomleft[0] - self.game.paddle.rect.topleft[0], -ball.rect.height)
        ball.anchor(self.game.paddle, pos)

class DuplicatePowerUp(PowerUp):

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_duplicate')

    def _activate(self):
        split_angle = 0.4  # radians
        for ball in list(self.game.balls):
            start_pos = ball.rect.center
            start_angle = ball.angle + split_angle
            if  start_angle >  2 * math.pi:
                start_angle -= 2 * math.pi
            ball1 = ball.clone(start_pos=start_pos, start_angle=start_angle)
            start_angle = abs(ball.angle - split_angle)
            ball2 = ball.clone(start_pos=start_pos, start_angle=start_angle)
            self.game.balls.append(ball1)
            self.game.balls.append(ball2)
            self.game.sprites.append(ball1)
            self.game.sprites.append(ball2)

    def deactivate(self):
        pass


class WarpPowerUp(PowerUp):

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_warp')

#
#
#
