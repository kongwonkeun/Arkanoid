#
#
#

import math
import random
import pygame

from arkanoid.utils.util import load_png

TWO_PI  = math.pi * 2
HALF_PI = math.pi / 2
RANDOM_RANGE = 0.1  # radians

class Ball(pygame.sprite.Sprite):

    def __init__(self, start_pos, start_angle, base_speed, top_speed = 15, normalisation_rate = 0.02, off_screen_callback = None):
        super().__init__()
        self.image, self.rect = load_png('ball')
        self.rect.x, self.rect.y = start_pos
        self.visible = True
        self.speed = base_speed
        self.base_speed = base_speed
        self.normalisation_rate = normalisation_rate
        self.angle = start_angle

        self._start_pos = start_pos
        self._start_angle = start_angle
        self._top_speed = top_speed
        self._off_screen_callback = off_screen_callback
        self._anchor = None
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self._collidable_sprites = pygame.sprite.Group()
        self._collision_data = {}

    def add_collidable_sprite(self, sprite, bounce_strategy = None, speed_adjust = 0.0, on_collide = None):
        self._collidable_sprites.add(sprite)
        self._collision_data[sprite] = (bounce_strategy, speed_adjust, on_collide)

    def remove_collidable_sprite(self, sprite):
        self._collidable_sprites.remove(sprite)
        try:
            del self._collision_data[sprite]
        except KeyError:
            pass

    def remove_all_collidable_sprites(self):
        self._collidable_sprites.empty()
        self._collision_data.clear()

    def clone(self, **kwargs):
        start_pos = kwargs.get('start_pos', self._start_pos)
        start_angle = kwargs.get('start_angle', self._start_angle)
        base_speed = kwargs.get('base_speed', self.base_speed)
        top_speed = kwargs.get('top_speed', self._top_speed)
        normalisation_rate = kwargs.get('normalisation_rate', self.normalisation_rate)
        off_screen_callback = kwargs.get('off_screen_callback', self._off_screen_callback)

        ball = Ball(start_pos, start_angle, base_speed, top_speed, normalisation_rate, off_screen_callback)

        for sprite in self._collidable_sprites:
            bounce_strategy, speed_adjust, on_collide = self._collision_data[sprite]
            ball.add_collidable_sprite(sprite, bounce_strategy, speed_adjust, on_collide)
        return ball

    def update(self):
        self.rect = self._calc_new_pos()
        if  self._area.contains(self.rect):
            if  not self._anchor:
                sprites_collided = pygame.sprite.spritecollide(self, (s for s in self._collidable_sprites if s.visible), False)
                if  sprites_collided:
                    self._handle_collision(sprites_collided)
                else:
                    self._normalise_speed()
        else:
            if  self._off_screen_callback:
                self._off_screen_callback(self)

    def _calc_new_pos(self):
        if  self._anchor:
            pos, rel_pos = self._anchor
            try:
                rect = pos.rect
            except AttributeError:
                return pygame.Rect(pos, (self.rect.width, self.rect.height))
            if  rel_pos:
                return pygame.Rect(rect.left + rel_pos[0], rect.top + rel_pos[1], self.rect.width, self.rect.height)
            return rect.center
        else:
            offset_x = self.speed * math.cos(self.angle)
            offset_y = self.speed * math.sin(self.angle)
            return self.rect.move(offset_x, offset_y)

    def _handle_collision(self, sprites):
        rects, bounce_strategy = [], None
        for sprite in sprites:
            rects.append(sprite.rect)
            if  not bounce_strategy:
                bounce_strategy = self._collision_data[sprite][0]
            if  self.speed < self._top_speed:
                self.speed += self._collision_data[sprite][1]
            on_collide = self._collision_data[sprite][2]
            if  on_collide:
                on_collide(sprite, self)
        if len(rects) == 1:
            if  bounce_strategy:
                self.angle = bounce_strategy(rects[0], self.rect)
            else:
                self.angle = self._calc_new_angle(rects)
        else:
            self.angle = self._calc_new_angle(rects)

    def _normalise_speed(self):
        if  self.speed >  self.base_speed:
            self.speed -= self.normalisation_rate
        else:
            self.speed += self.normalisation_rate

    def _calc_new_angle(self, rects):
        tl, tr, bl, br = self._determine_collide_points(rects)
        angle = self.angle
        if  [tl, tr, bl, br].count(True) in (1, 3, 4):
            if  self.angle > math.pi:
                angle = self.angle - math.pi
            else:
                angle = self.angle + math.pi
            if  [tl, tr, bl, br].count(True) == 1:
                angle += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)
        else:
            top_collision = tl and tr and self.angle > math.pi
            bottom_collision = bl and br and self.angle < math.pi
            if  top_collision or bottom_collision:
                angle = TWO_PI - self.angle
                if  (TWO_PI - HALF_PI - 0.06) < angle < (TWO_PI - HALF_PI + 0.06):
                    angle += 0.35
                elif (HALF_PI + 0.06) > angle > (HALF_PI - 0.06):
                    angle += 0.35
            else:
                left_collision = (tl and bl and HALF_PI < self.angle < TWO_PI - HALF_PI)
                right_collision = tr and br and ( self.angle > TWO_PI - HALF_PI or self.angle < HALF_PI)
                if  left_collision or right_collision:
                    if  self.angle < math.pi:
                        angle = math.pi - self.angle
                    else:
                        angle = (TWO_PI - self.angle) + math.pi
                    if  math.pi - 0.06 < angle < math.pi + 0.06:
                        angle += 0.35
                    elif angle > TWO_PI - 0.06:
                        angle -= 0.35
                    elif angle < 0.06:
                        angle += 0.35
            angle += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)
        angle = round(angle, 2)
        return angle

    def _determine_collide_points(self, rects):
        tl, tr, bl, br = False, False, False, False
        for rect in rects:
            tl = tl or rect.collidepoint(self.rect.topleft)
            tr = tr or rect.collidepoint(self.rect.topright)
            bl = bl or rect.collidepoint(self.rect.bottomleft)
            br = br or rect.collidepoint(self.rect.bottomright)
        if  [tl, tr, bl, br].count(True) == 1:
            if  tl:
                if  self.angle > TWO_PI - HALF_PI:
                    tr = True
                elif self.angle < math.pi:
                    bl = True
            elif tr:
                if  math.pi < self.angle < TWO_PI - HALF_PI:
                    tl = True
                elif self.angle < HALF_PI:
                    br = True
            elif bl:
                if  self.angle < HALF_PI:
                    br = True
                elif self.angle > math.pi:
                    tl = True
            elif br:
                if  math.pi > self.angle > HALF_PI:
                    bl = True
                elif self.angle > TWO_PI - HALF_PI:
                    tr = True
            if  [tl, tr, bl, br].count(True) > 1:
                pass
        return tl, tr, bl, br

    def anchor(self, pos, rel_pos = None):
        self._anchor = pos, rel_pos

    def release(self, angle = None):
        if  angle:
            self.angle = angle
        self.speed = self.base_speed
        self._anchor = None

    def reset(self):
        self.rect.midbottom = self._start_pos
        self.speed = self.base_speed
        self.visible = True
        self.angle = self._start_angle
        self._anchor = None

#
#
#
