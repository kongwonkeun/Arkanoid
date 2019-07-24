#
#
#

import enum
import itertools
import logging
import math
import random
import weakref
import pygame

from arkanoid.utils.util import load_png_sequence

SPEED = 2
START_DIRECTION = 1.57  # radians
START_DURATION = 75  # frames
MIN_DURATION = 30
MAX_DURATION = 60
RANDOM_RANGE = 1.5  # radians
TWO_PI  = math.pi * 2
HALF_PI = math.pi / 2

class EnemyType(enum.Enum):
    cube = 'enemy_cube'
    cone = 'enemy_cone'
    molecule = 'enemy_molecule'
    pyramid = 'enemy_pyramid'
    sphere = 'enemy_sphere'

class Enemy(pygame.sprite.Sprite):

    _enemies = weakref.WeakSet()

    def __init__(self, enemy_type, paddle, on_paddle_collide, collidable_sprites, on_destroyed):
        super().__init__()
        self._enemies.add(self)
        self._paddle = paddle
        self._on_paddle_collide = on_paddle_collide
        self._on_destroyed = on_destroyed
        self._on_destroyed_called = False
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self._animation, width, height = self._load_animation_sequence(enemy_type.value)
        self.rect = pygame.Rect(self._area.center, (width, height))
        self.image = None
        self._explode_animation = None
        self._collidable_sprites = pygame.sprite.Group()
        for sprite in collidable_sprites:
            self._collidable_sprites.add(sprite)
        self._direction = START_DIRECTION
        self._duration = START_DURATION
        self._last_contact = 0
        self.freeze = False
        self._update_count = 0
        self.visible = True

    def _load_animation_sequence(self, filename_prefix):
        sequence = load_png_sequence(filename_prefix)
        max_width, max_height = 0, 0
        for image, rect in sequence:
            if  rect.width > max_width:
                max_width = rect.width
            if  rect.height > max_height:
                max_height = rect.height
        return itertools.cycle(sequence), max_width, max_height

    def update(self):
        if  self._explode_animation:
            self._explode()
        else:
            if  self._update_count % 4 == 0:
                self.image, _ = next(self._animation)
            if  not self.freeze:
                self.rect = self._calc_new_position()
                if  self._area.contains(self.rect):
                    if  pygame.sprite.spritecollide(self, [self._paddle], False):
                        self._on_paddle_collide(self, self._paddle)
                    else:
                        visible_sprites = itertools.chain(
                            (sprite for sprite in self._collidable_sprites if sprite.visible),
                            (sprite for sprite in self._enemies if sprite.visible and sprite is not self)
                        )
                        sprites_collided = pygame.sprite.spritecollide(self, visible_sprites, None)
                        if  sprites_collided:
                            self._last_contact = self._update_count
                            self._direction = self._calc_direction_collision(sprites_collided)
                        elif self._update_count > self._last_contact + 30:
                            if  not self._duration:
                                self._direction = self._calc_direction()
                                self._duration = (self._update_count + random.choice(range(MIN_DURATION, MAX_DURATION)))
                            elif self._update_count >= self._duration:
                                self._duration = 0
                else:
                    if  not self._on_destroyed_called:
                        self._on_destroyed(self)
                        self._on_destroyed_called = True
        self._update_count += 1

    def _explode(self):
        try:
            if  self._update_count % 2 == 0:
                rect = self.rect
                self.image, self.rect = next(self._explode_animation)
                self.rect.center = rect.center
        except StopIteration:
            self._explode_animation = None
            self._on_destroyed(self)

    def _calc_new_position(self):
        offset_x = SPEED * math.cos(self._direction)
        offset_y = SPEED * math.sin(self._direction)
        return self.rect.move(offset_x, offset_y)

    def _calc_direction_collision(self, sprites_collided):
        top    = pygame.Rect(self.rect.left + 5, self.rect.top, self.rect.width - 10, 5)
        left   = pygame.Rect(self.rect.left, self.rect.top + 5, 5, self.rect.height - 10)
        bottom = pygame.Rect(self.rect.left + 5, self.rect.top + self.rect.height - 5, self.rect.width - 10, 5)
        right  = pygame.Rect(self.rect.left + self.rect.width - 5, self.rect.top + 5, 5, self.rect.height - 10)
        rects  = [sprite.rect for sprite in sprites_collided]
        cleft, cright, ctop, cbottom = False, False, False, False
        for rect in rects:
            cleft = cleft or left.colliderect(rect)
            cright = cright or right.colliderect(rect)
            ctop = ctop or top.colliderect(rect)
            cbottom = cbottom or bottom.colliderect(rect)
        direction = self._direction
        if  cleft and cright and ctop and cbottom:
            direction = -direction
        elif cleft and cright and cbottom:
            direction = math.pi + HALF_PI
        elif cleft and cright and ctop:
            direction = HALF_PI
        elif cleft and cbottom:
            direction = 0
        elif cright and cbottom:
            direction = math.pi
        elif cbottom:
            if  direction not in (0, math.pi):
                direction = 0
        else:
            direction = math.pi - HALF_PI
            if  cleft or cright:
                if  self._update_count % 60 == 0:
                    if  cright:
                        direction = math.pi
                    else:
                        direction = 0
        return direction

    def _calc_direction(self):
        paddle_x, paddle_y = self._paddle.rect.center
        direction = math.atan2(paddle_y - self.rect.y, paddle_x - self.rect.x)
        direction += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)
        return direction

    def explode(self):
        if  not self._explode_animation:
            self._explode_animation = iter(load_png_sequence('enemy_explosion'))

    def reset(self):
        self._direction = START_DIRECTION
        self._duration = START_DURATION
        self._on_destroyed_called = False
        self.visible = True
        self.freeze = False

#
#
#
