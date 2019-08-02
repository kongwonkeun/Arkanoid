#
#
#

import itertools
import math
import pygame

from arkanoid.event import receiver
from arkanoid.utils.util import (load_png, load_png_sequence, load_png_x, load_png_sequence_x) #---- kong ----
from arkanoid.sensor import G_direction

class Paddle(pygame.sprite.Sprite):

    def __init__(self, left_offset = 0, right_offset = 0, bottom_offset = 0, speed = 10, game = None): #---- kong ----
        super().__init__()
        #---- kong ----
        self.game = game
        #----
        self.speed = speed
        self._move = 0
        self.visible = True
        self.image, self.rect = load_png_x('paddle') #---- kong ----
        screen = pygame.display.get_surface().get_rect()
        self.area = pygame.Rect(
            screen.left + left_offset,
            screen.height - bottom_offset,
            screen.width - left_offset - right_offset,
            self.rect.height
        )
        self.rect.center = self.area.center
        self.ball_collide_callbacks = []
        self._state = NormalState(self)

    def update(self):
        #---- kong ----
        #global G_direction
        #if   G_direction == -1: self._move = -self.speed # left
        #elif G_direction ==  1: self._move =  self.speed # right
        #elif G_direction ==  0: self._move = 0
        #else: pass
        #----
        self._state.update()
        if  self._move:
            newpos = self.rect.move(self._move, 0)
            if  self._area_contains(newpos):
                self.rect = newpos
            else:
                while self._move != 0:
                    if  self._move <  0:
                        self._move += 1
                    else:
                        self._move -= 1
                    newpos = self.rect.move(self._move, 0)
                    if  self._area_contains(newpos):
                        self.rect = newpos
                        break

    def _area_contains(self, newpos):
        return self.area.collidepoint(newpos.midleft) and self.area.collidepoint(newpos.midright)

    def transition(self, state):

        def on_exit():
            self._state = state
            state.enter()
        self._state.exit(on_exit)

    def move_left(self):
        self._move = -self.speed

    def move_right(self):
        self._move = self.speed

    def stop(self):
        self._move = 0

    def reset(self):
        self.rect.center = self.area.center

    def on_ball_collide(self, paddle, ball):
        for callback in self.ball_collide_callbacks:
            callback(ball)

    @property
    def exploding(self):
        return isinstance(self._state, ExplodingState)

    @staticmethod
    def bounce_strategy(paddle_rect, ball_rect):
        segment_size = paddle_rect.width // 6
        segments = []
        for i in range(6):
            left = paddle_rect.left + segment_size * i
            if  i < 5:
                segment = pygame.Rect(left, paddle_rect.top, segment_size, paddle_rect.height)
            else:
                segment = pygame.Rect(
                    left, 
                    paddle_rect.top,
                    paddle_rect.width - (segment_size * 5),
                    paddle_rect.height
                )
            segments.append(segment)
        angles = 220, 245, 260, 280, 295, 320
        index = ball_rect.collidelist(segments)
        return math.radians(angles[index])

class PaddleState:

    def __init__(self, paddle):
        self.paddle = paddle

    def enter(self):
        pass

    def update(self):
        raise NotImplementedError('subclasses must implement update()')

    def exit(self, on_exit):
        on_exit()

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r})'.format(class_name, self.paddle)


class NormalState(PaddleState):

    def __init__(self, paddle):
        super().__init__(paddle)
        self._pulsator = _PaddlePulsator(paddle, 'paddle_pulsate')
        #---- kong ----
        self._game = paddle.game
        self._bullets = []
        self._flag = True
        #----

    def enter(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = load_png_x('paddle') #---- kong ----
        self.paddle.rect.center = pos

    def update(self):
        self._pulsator.update()
        #---- kong ----
        #if  self._flag:
        #    self._flag = False
        #    receiver.register_handler(pygame.KEYUP, self._fire)
        #----

    #---- kong ----
    def _fire(self, event):
        if  event.key == pygame.K_SPACE:
            self._bullets = [bullet for bullet in self._bullets if bullet.visible]
            if  len(self._bullets) < 3:
                left, top = self.paddle.rect.bottomleft
                bullet = LaserBullet(self._game, position=(left + (self.paddle.rect.width /2), top))
                self._bullets.append(bullet)
                self._game.sprites.append(bullet)
                bullet.release()
    #----

class _PaddlePulsator:

    def __init__(self, paddle, image_sequence_name):
        self._paddle = paddle
        self._image_sequence = load_png_sequence_x(image_sequence_name) #---- kong ----
        self._animation = None
        self._update_count = 0

    def update(self):
        if  self._update_count % 80 == 0:
            self._animation = itertools.chain(self._image_sequence, reversed(self._image_sequence))
            self._update_count = 0
        elif self._animation:
            try:
                if  self._update_count % 4 == 0:
                    self._paddle.image, _ = next(self._animation)
            except StopIteration:
                self._animation = None
        self._update_count += 1

class MaterializeState(PaddleState):

    def __init__(self, paddle):
        super().__init__(paddle)
        self._animation = iter(load_png_sequence_x('paddle_materialize')) #---- kong ----
        self._update_count = 0

    def update(self):
        if  self._update_count % 2 == 0:
            try:
                pos = self.paddle.rect.center
                self.paddle.image, self.paddle.rect = next(self._animation)
                self.paddle.rect.center = pos
            except StopIteration:
                self.paddle.transition(NormalState(self.paddle))
        self._update_count += 1

class WideState(PaddleState):

    def __init__(self, paddle):
        super().__init__(paddle)
        self._image_sequence = load_png_sequence_x('paddle_wide') #---- kong ----
        self._animation = iter(self._image_sequence)
        self._pulsator = _PaddlePulsator(paddle, 'paddle_wide_pulsate')
        self._expand, self._shrink = True, False
        self._on_exit = None

    def update(self):
        if  not self._expand and not self._shrink:
            self._pulsator.update()
        if  self._expand:
            self._expand_paddle()
        elif self._shrink:
            self._shrink_paddle()

    def _expand_paddle(self):
        try:
            self._convert()
            while (not self.paddle.area.collidepoint(self.paddle.rect.midleft)):
                self.paddle.rect = self.paddle.rect.move(1, 0)
            while (not self.paddle.area.collidepoint(self.paddle.rect.midright)):
                self.paddle.rect = self.paddle.rect.move(-1, 0)
        except StopIteration:
            self._expand = False

    def _shrink_paddle(self):
        try:
            self._convert()
        except StopIteration:
            self._shrink = False
            self._on_exit()

    def _convert(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = next(self._animation)
        self.paddle.rect.center = pos

    def exit(self, on_exit):
        self._shrink = True
        self._on_exit = on_exit
        self._animation = iter(reversed(self._image_sequence))

class LaserState(PaddleState):

    def __init__(self, paddle, game):
        super().__init__(paddle)
        self._game = game
        self._image_sequence = load_png_sequence_x('paddle_laser') #---- kong ----
        self._laser_anim = iter(self._image_sequence)
        self._to_laser, self._from_laser = True, False
        self._pulsator = _PaddlePulsator(paddle, 'paddle_laser_pulsate')
        self._bullets = []
        self._on_exit = None
        #---- kong ----
        self._fire_count = 0
        #----

    def update(self):
        if  not self._to_laser and not self._from_laser:
            self._pulsator.update()
        if  self._to_laser:
            self._convert_to_laser()
        elif self._from_laser:
            self._convert_from_laser()
        self._fire_count += 1
        if  self._fire_count % 20 == 0:
            self._fire_x()

    def _convert_to_laser(self):
        try:
            self._convert()
        except StopIteration:
            self._to_laser = False
            receiver.register_handler(pygame.KEYUP, self._fire)

    def _convert_from_laser(self):
        try:
            self._convert()
        except StopIteration:
            self._from_laser = False
            self._on_exit()

    def _convert(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = next(self._laser_anim)
        self.paddle.rect.center = pos
        while (not self.paddle.area.collidepoint(self.paddle.rect.midleft)):
            self.paddle.rect = self.paddle.rect.move(1, 0)
        while (not self.paddle.area.collidepoint(self.paddle.rect.midright)):
            self.paddle.rect = self.paddle.rect.move(-1, 0)

    def exit(self, on_exit):
        self._to_laser = False
        self._from_laser = True
        self._on_exit = on_exit
        self._laser_anim = iter(reversed(self._image_sequence))
        receiver.unregister_handler(self._fire)

    #---- kong ----

    def _fire_x(self):
        self._bullets = [bullet for bullet in self._bullets if bullet.visible]
        if  len(self._bullets) < 3:
            left, top = self.paddle.rect.bottomleft
            bullet1 = LaserBullet(self._game, position = (left + 15, top))
            bullet2 = LaserBullet(self._game, position = (left + self.paddle.rect.width - 15, top))
            bullet3 = LaserBullet(self._game, position = (left + self.paddle.rect.width / 2,  top))
            self._bullets.append(bullet1)
            self._bullets.append(bullet2)
            self._bullets.append(bullet3)
            self._game.sprites.append(bullet1)
            self._game.sprites.append(bullet2)
            self._game.sprites.append(bullet3)
            bullet1.release()
            bullet2.release()
            bullet3.release()
    #----

    def _fire(self, event):
        if  event.key == pygame.K_SPACE:
            self._bullets = [bullet for bullet in self._bullets if bullet.visible]
            if  len(self._bullets) < 3:
                left, top = self.paddle.rect.bottomleft
                bullet1 = LaserBullet(self._game, position = (left + 10, top))
                bullet2 = LaserBullet(self._game, position = (left + self.paddle.rect.width - 10, top))
                self._bullets.append(bullet1)
                self._bullets.append(bullet2)
                self._game.sprites.append(bullet1)
                self._game.sprites.append(bullet2)
                bullet1.release()
                bullet2.release()

class LaserBullet(pygame.sprite.Sprite):

    def __init__(self, game, position, speed = 15):
        super().__init__()
        self.image, self.rect = load_png('laser_bullet')
        self._game = game
        self._position = position
        self._speed = speed
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self.visible = False

    def release(self):
        self.rect.midbottom = self._position
        self.visible = True

    def update(self):
        if  self.visible:
            self.rect = self.rect.move(0, -self._speed)
            top_edge_collision = pygame.sprite.spritecollide(self, [self._game.round.edges.top], False)

            if  not top_edge_collision:
                visible_bricks = (brick for brick in self._game.round.bricks if brick.visible)
                brick_collide = pygame.sprite.spritecollide(self, visible_bricks, False)
                if  brick_collide:
                    brick = brick_collide[0]
                    brick.value = 0
                    brick.powerup_cls = None
                    self._game.on_brick_collide(brick, self)
                    self.visible = False
                else:
                    visible_enemies = (enemy for enemy in self._game.enemies if enemy.visible)
                    enemy_collide = pygame.sprite.spritecollide(self, visible_enemies, False)
                    if  enemy_collide:
                        self._game.on_enemy_collide(enemy_collide[0], self)
                        self.visible = False
            else:
                self.visible = False


class ExplodingState(PaddleState):

    def __init__(self, paddle, on_exploded):
        super().__init__(paddle)
        self._exploding_animation = iter(load_png_sequence_x('paddle_explode')) #---- kong ----
        self._on_explode_complete = on_exploded
        self._rect_orig = None
        self._update_count = 0

    def enter(self):
        self._rect_orig = self.paddle.rect

    def update(self):
        if  10 < self._update_count:
            if  self._update_count % 4 == 0:
                try:
                    self.paddle.image, self.paddle.rect = next(self._exploding_animation)
                    self.paddle.rect.center = self._rect_orig.center
                except StopIteration:
                    self._on_explode_complete()
                    self.paddle.visible = False
        self.paddle.stop()
        self._update_count += 1

#
#
#
