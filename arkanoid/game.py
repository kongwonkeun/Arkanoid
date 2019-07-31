#
#

import sys
import functools
import importlib
import itertools
import os
import random
import pygame

from arkanoid.event import receiver
from arkanoid.rounds.round1 import Round1
from arkanoid.sprites.ball import Ball
from arkanoid.sprites.enemy import Enemy
from arkanoid.sprites.paddle import (ExplodingState, Paddle, MaterializeState)
from arkanoid.utils.util import (load_high_score, load_png, load_png_sequence, save_high_score)
from arkanoid.utils import ptext
from arkanoid.sensor import SensorThread

GAME_SPEED = 60
DISPLAY_SIZE = 600, 800
TOP_OFFSET = 150
DISPLAY_CAPTION = 'Arkanoid'
BALL_START_ANGLE_RAD = 5.0

#BALL_BASE_SPEED = 8  # pixels per frame
#BALL_TOP_SPEED = 15  # pixels per frame
#BALL_SPEED_NORMALISATION_RATE = 0.02
#BRICK_SPEED_ADJUST = 0.5
#WALL_SPEED_ADJUST = 0.2
#PADDLE_SPEED = 10
BALL_BASE_SPEED = 5
BALL_TOP_SPEED = 10
BALL_SPEED_NORMALISATION_RATE = 0.02
BRICK_SPEED_ADJUST = 0.3
WALL_SPEED_ADJUST = 0.1
PADDLE_SPEED = 10

MAIN_FONT = os.path.join(os.path.dirname(__file__), 'data', 'fonts', 'generation.ttf')
ALT_FONT  = os.path.join(os.path.dirname(__file__), 'data', 'fonts', 'optimus.otf')

pygame.init()

class Arkanoid:

    def __init__(self, sensor):
        self._sensor = sensor
        self._clock = pygame.time.Clock()
        self._screen = self._create_screen()
        self._background = self._create_background()
        self._display_logo()
        self._display_score_titles()
        self._high_score = load_high_score()
        self._start_screen = StartScreen(self._start_game, sensor)
        self._game = None
        self._running = True

        def quit_handler(event):
            self._running = False
        receiver.register_handler(pygame.QUIT, quit_handler)

        self._display_player_score = functools.partial(self._display_score, y = 35)
        self._display_high_score = functools.partial(self._display_score, y = 100)
        self._display_player_score(0)
        self._display_high_score(self._high_score)

    def main_loop(self):
        while self._running:
            self._clock.tick(GAME_SPEED)
            receiver.receive() # run each handler

            if  not self._game:
                self._start_screen.show()
            else:
                self._game.update() # update game state
                self._display_player_score(self._game.score)
                if  self._game.over:
                    if  self._game.score > self._high_score:
                        self._high_score = self._game.score
                        self._display_high_score(self._high_score)
                        save_high_score(self._high_score)
                    self._game = None
            pygame.display.flip()

    def _start_game(self, round_no):
        module_name = 'arkanoid.rounds.round{}'.format(round_no)
        try:
            module = importlib.import_module(module_name)
            round_cls = getattr(module, 'Round{}'.format(round_no))
        except (ImportError, AttributeError):
            print('unable to import round')
        else:
            self._game = Game(self._sensor, round_class = round_cls)
            self._start_screen.hide()

    def _create_screen(self):
        #pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_mode(DISPLAY_SIZE, pygame.FULLSCREEN) #---- kong ----
        pygame.display.set_caption(DISPLAY_CAPTION)
        pygame.mouse.set_visible(False)
        screen = pygame.display.get_surface()
        return screen

    def _create_background(self):
        background = pygame.Surface(self._screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))
        return background

    def _display_logo(self):
        image, _ = load_png('logo.png')
        self._screen.blit(image, (5, 0))

    def _display_score_titles(self):
        ptext.draw(
            '1UP',
            (self._screen.get_width() - 70, 10),
            fontname = MAIN_FONT,
            fontsize = 24,
            color = (230, 0, 0)
        )
        ptext.draw(
            'HIGH SCORE',
            (self._screen.get_width() - 205, 75),
            fontname = MAIN_FONT,
            fontsize = 24,
            color = (230, 0, 0)
        )

    def _display_score(self, value, y):
        score_surf = pygame.Surface((150, 20)).convert_alpha()
        ptext.draw(
            str(value),
            topright = (150, 0),
            fontname = MAIN_FONT,
            fontsize = 24,
            color = (255, 255, 255),
            surf = score_surf
        )
        position = self._screen.get_width() - 160, y
        self._screen.blit(self._background, position, score_surf.get_rect())
        self._screen.blit(score_surf, position)

class StartScreen:

    def __init__(self, on_start, sensor):
        self._sensor = sensor
        self._on_start = on_start # callback ptr
        self._screen = pygame.display.get_surface()
        self._init = False
        self._powerups = (
            (itertools.cycle(load_png_sequence('powerup_laser')), 'laser', 'enables the vaus\nto fire a laser'),
            (itertools.cycle(load_png_sequence('powerup_slow')), 'slow', 'slow down the\nenergy ball'),
            (itertools.cycle(load_png_sequence('powerup_life')), 'extra life', 'gain an additional\nvaus'),
            (itertools.cycle(load_png_sequence('powerup_expand')), 'expand', 'expands the vaus'),
            (itertools.cycle(load_png_sequence('powerup_catch')), 'catch', 'catches the energy\nball'),
            (itertools.cycle(load_png_sequence('powerup_duplicate')), 'duplicate', 'duplicates the energy\nball')
        )
        self._registered = False
        self._text_colors_1 = itertools.cycle([(255, 255, 255), (255, 255, 0)])
        self._text_color_1 = None
        self._text_colors_2 = itertools.cycle([(255, 255, 0), (255, 0, 0)])
        self._text_color_2 = None
        self._user_input = ''
        self._user_input_pos = None
        self._display_count = 0

    def show(self):
        if  not self._registered:
            receiver.register_handler(pygame.KEYUP, self._on_keyup)
            self._registered = True
        if  not self._init:
            self._init = True
            self._screen.blit(pygame.Surface((600, 650)), (0, TOP_OFFSET))
        ptext.draw(
            'POWERUPS', 
            (210, 200),
            fontname = ALT_FONT,
            fontsize = 32,
            color = (255, 255, 255)
        )
        left, top = 30, 270
        for anim, name, desc in self._powerups:
            if  self._display_count % 4 == 0:
                image, _ = next(anim)
                self._screen.blit(image, (left, top))
                ptext.draw(
                    name.upper(),
                    (left + image.get_width() + 20, top - 3),
                    fontname = ALT_FONT,
                    fontsize = 20,
                    color = (255, 255, 255)
                )
                ptext.draw(
                    desc.upper(),
                    (left, top + 25),
                    fontname = ALT_FONT,
                    fontsize = 14,
                    color = (255, 255, 255)
                )
            left += 180
            if  left > 400:
                left = 30
                top += 100

        if  self._display_count % 15 == 0:
            self._text_color_1 = next(self._text_colors_1)
            self._text_color_2 = next(self._text_colors_2)
        ptext.draw(
            'SPACEBAR TO START',
            (50, 500),
            fontname = ALT_FONT,
            fontsize = 48,
            color = self._text_color_1,
            shadow = (1.0, 1.0),
            scolor = "grey"
        )
        ptext.draw(
            'OR ENTER LEVEL',
            (160, 575),
            fontname = ALT_FONT,
            fontsize = 32,
            color = self._text_color_2
        )
        self._user_input_pos = ptext.draw(
            self._user_input,
            (280, 625),
            fontname = ALT_FONT,
            fontsize = 40,
            color = (255, 255, 255)
        )[1]
        ptext.draw(
            'Based on original Arkanoid game\nby Taito Corporation 1986',
            (100, 700),
            align = 'center',
            fontname = ALT_FONT,
            fontsize = 24,
            color = (128, 128, 128)
        )
        self._display_count += 1

    def hide(self):
        receiver.unregister_handler(self._on_keyup)
        self._registered = False
        self._init = False

    def _on_keyup(self, event):
        numeric_keys = {
            pygame.K_0: '0', pygame.K_1: '1', pygame.K_2: '2',
            pygame.K_3: '3', pygame.K_4: '4', pygame.K_5: '5',
            pygame.K_6: '6', pygame.K_7: '7', pygame.K_8: '8',
            pygame.K_9: '9'
        }
        if  event.key == pygame.K_SPACE:
            self._on_start(1)
        elif event.key in numeric_keys and len(self._user_input) < 2:
            self._user_input += numeric_keys[event.key]
        elif event.key == pygame.K_BACKSPACE:
            self._user_input = ''
            self._screen.blit(pygame.Surface((50, 50)), self._user_input_pos)
        elif event.key == pygame.K_RETURN and self._user_input:
            self._screen.blit(pygame.Surface((50, 50)), self._user_input_pos)
            self._on_start(int(self._user_input))
            self._user_input = ''
        #---- kong ----
        elif event.key == pygame.K_ESCAPE:
            self._sensor.stop()
            sys.exit()
        #----

class Game:

    def __init__(self, sensor, round_class = Round1, lives = 3):
        self.lives = lives
        self.score = 0

        self._sensor = sensor
        self._screen = pygame.display.get_surface()
        self._life_img, _ = load_png('paddle_life.png')
        self._life_rects = []

        self.round = round_class(TOP_OFFSET)
        self.paddle = Paddle(
            left_offset = self.round.edges.left.rect.width,
            right_offset = self.round.edges.right.rect.width,
            bottom_offset = 60,
            speed = PADDLE_SPEED,
            game = self
        )
        ball = Ball(
            start_pos = self.paddle.rect.midtop,
            start_angle = BALL_START_ANGLE_RAD,
            base_speed = BALL_BASE_SPEED,
            top_speed = BALL_TOP_SPEED,
            normalisation_rate = BALL_SPEED_NORMALISATION_RATE,
            off_screen_callback = self._off_screen
        )
        self.balls = [ball]
        self.active_powerup = None
        self.enemies = []
        self.sprites = []
        self._create_event_handlers()
        self.over = False
        self.state = GameStartState(self)

    def update(self):
        self.state.update()
        self._update_sprites()
        self._update_lives()

    def _update_sprites(self):
        for sprite in self.sprites:
            self._screen.blit(self.round.background, sprite.rect, sprite.rect)
        for sprite in self.sprites:
            sprite.update()
            if  sprite.visible:
                self._screen.blit(sprite.image, sprite.rect)

    def _update_lives(self):
        for rect in self._life_rects:
            self._screen.blit(self.round.background, rect, rect)
        self._life_rects.clear()

        left = self.round.edges.left.rect.width
        top = self._screen.get_height() - self._life_img.get_height() - 5
        for life in range(self.lives - 1):
            self._life_rects.append(self._screen.blit(self._life_img, (left, top)))
            left += self._life_img.get_width() + 5

    def on_brick_collide(self, brick, sprite):
        brick.collision_count += 1
        if  brick.visible:
            brick.animate()
        else:
            if  brick.value:
                self.score += brick.value
            self.round.brick_destroyed()
        if  brick.powerup_cls:
            release = not brick.visible
            if  not release:
                release = random.choice((True, False))
            if  release:
                powerup = brick.powerup_cls(self, brick)
                brick.powerup_cls = None
                self.sprites.append(powerup)
        if  not self.enemies and self.round.can_release_enemies():
            self._setup_enemies()
            for enemy in self.enemies:
                self.release_enemy(enemy)

    def on_enemy_collide(self, enemy, sprite):
        enemy.explode()
        self.score += 500
        for ball in self.balls:
            ball.remove_collidable_sprite(enemy)

    def _setup_enemies(self):
        collidable_sprites = []
        collidable_sprites += self.round.edges
        collidable_sprites += self.round.bricks
        for _ in range(self.round.num_enemies):
            enemy_sprite = Enemy(
                self.round.enemy_type,
                self.paddle,
                self.on_enemy_collide,
                collidable_sprites,
                on_destroyed=self.release_enemy
            )
            self.enemies.append(enemy_sprite)
            self.sprites.append(enemy_sprite)

    def release_enemy(self, enemy):
        enemy.freeze = True
        enemy.visible = False

        def door_open(coords):
            enemy.reset()
            enemy.rect.topleft = coords
            for ball in self.balls:
                ball.add_collidable_sprite(enemy, on_collide=self.on_enemy_collide)
        self.round.edges.top.open_door(door_open)

    def _off_screen(self, ball):
        if  len(self.balls) > 1:
            self.balls.remove(ball)
            self.sprites.remove(ball)
            ball.visible = False
        else:
            if  not isinstance(self.state, BallOffScreenState):
                self.state = BallOffScreenState(self)

    def _create_event_handlers(self):
        keys_down = 0

        def move_left(event):
            nonlocal keys_down
            if  event.key == pygame.K_LEFT:
                self.paddle.move_left()
                keys_down += 1
        self.handler_move_left = move_left

        def move_right(event):
            nonlocal keys_down
            if  event.key == pygame.K_RIGHT:
                self.paddle.move_right()
                keys_down += 1
        self.handler_move_right = move_right

        def stop(event):
            nonlocal keys_down
            if  event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                if  keys_down > 0:
                    keys_down -= 1
                if  keys_down == 0:
                    self.paddle.stop()
        self.handler_stop = stop

        #---- kong ----
        def quit(event):
            nonlocal keys_down
            if  event.key == pygame.K_ESCAPE:
                self._sensor.stop()
                sys.exit()
        self.handler_quit = quit
        #----

    @property
    def ball(self):
        try:
            return self.balls[0]
        except IndexError:
            return None

    def __repr__(self):
        class_name = type(self).__name__
        return '{}(round_class={}, lives={})'.format(class_name, type(self.round).__name__, self.lives)

class BaseState:

    def __init__(self, game):
        self.game = game

    def update(self):
        raise NotImplementedError('subclasses must implement update()')

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r})'.format(class_name, self.game)

class GameStartState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        self.game.paddle.visible = False
        self.game.ball.visible = False
        receiver.register_handler(pygame.KEYDOWN, self.game.handler_move_left, self.game.handler_move_right)
        receiver.register_handler(pygame.KEYUP, self.game.handler_stop)
        #---- kong ----
        receiver.register_handler(pygame.KEYUP, self.game.handler_quit)
        #----

    def update(self):
        self.game.state = RoundStartState(self.game)

class RoundStartState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        self._setup_sprites()
        self._configure_ball()
        self._configure_paddle()
        self._screen = pygame.display.get_surface()
        self.game.ball.reset()
        self.game.paddle.visible = False
        self.game.ball.visible = False
        self.game.ball.anchor((self._screen.get_width() / 2, self._screen.get_height() - 100))
        self._paddle_reset = False
        self._update_count = 0

    def _setup_sprites(self):
        self.game.sprites.clear()
        self.game.sprites.append(self.game.paddle)
        self.game.sprites.append(self.game.ball)
        self.game.sprites += self.game.round.edges
        self.game.sprites += self.game.round.bricks

    def _configure_ball(self):
        self.game.ball.remove_all_collidable_sprites()
        for edge in self.game.round.edges:
            self.game.ball.add_collidable_sprite(edge, speed_adjust = WALL_SPEED_ADJUST)
        self.game.ball.add_collidable_sprite(
            self.game.paddle, 
            bounce_strategy = self.game.paddle.bounce_strategy,
            on_collide = self.game.paddle.on_ball_collide
        )
        for brick in self.game.round.bricks:
            self.game.ball.add_collidable_sprite(
                brick,
                speed_adjust = BRICK_SPEED_ADJUST,
                on_collide = self.game.on_brick_collide
            )
        self.game.ball.base_speed += self.game.round.ball_base_speed_adjust
        self.game.ball.normalisation_rate += self.game.round.ball_speed_normalisation_rate_adjust

    def _configure_paddle(self):
        self.game.paddle.speed += self.game.round.paddle_speed_adjust

    def update(self):
        caption, ready = None, None
        if  self._update_count > 100:
            caption = ptext.draw(
                self.game.round.name,
                (235, self.game.paddle.rect.center[1] - 150),
                fontname = MAIN_FONT,
                fontsize = 24,
                color = (255, 255, 255)
            )
        if  self._update_count > 200:
            ready = ptext.draw(
                'ready',
                (250, caption[1][1] + 50),
                fontname = MAIN_FONT,
                fontsize = 24,
                color = (255, 255, 255)
            )
            self.game.ball.anchor(self.game.paddle, (self.game.paddle.rect.width // 2, -self.game.ball.rect.height))
            if  not self._paddle_reset:
                self.game.paddle.reset()
                self._paddle_reset = True
            self.game.paddle.visible = True
            self.game.ball.visible = True
        if  self._update_count == 201:
            self.game.paddle.transition(MaterializeState(self.game.paddle))
            for brick in self.game.round.bricks:
                brick.animate()
        if  self._update_count > 310:
            self._screen.blit(self.game.round.background, caption[1])
            self._screen.blit(self.game.round.background, ready[1])
        if  self._update_count > 340:
            self.game.ball.release(BALL_START_ANGLE_RAD)
            self.game.state = RoundPlayState(self.game)
        self._update_count += 1
        if  not self.game.paddle.visible:
            self.game.paddle.stop()

class RoundPlayState(BaseState):

    def __init__(self, game):
        super().__init__(game)

    def update(self):
        if  self.game.round.complete:
            self.game.state = RoundEndState(self.game)

class BallOffScreenState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        if  self.game.active_powerup:
            self.game.active_powerup.deactivate()
            self.game.active_powerup = None
        self.game.paddle.transition(ExplodingState(self.game.paddle, self._exploded))
        self._explode_complete = False

    def update(self):
        if  self._explode_complete:
            if  self.game.lives - 1 > 0:
                self.game.state = RoundRestartState(self.game)
            else:
                self.game.state = GameEndState(self.game)

    def _exploded(self):
        self._explode_complete = True

class RoundRestartState(RoundStartState):

    def __init__(self, game):
        super().__init__(game)
        self._lives = game.lives - 1
        for enemy in self.game.enemies:
            enemy.freeze = True
            enemy.visible = False
        self.game.round.edges.top.cancel_open_door()
        self._enemies_rereleased = False

    def _setup_sprites(self):
        pass

    def _configure_ball(self):
        pass

    def _configure_paddle(self):
        pass

    def update(self):
        super().update()
        if  self._update_count > 100:
            self.game.lives = self._lives
        if  self._update_count > 340:
            if  not self._enemies_rereleased:
                for enemy in self.game.enemies:
                    self.game.release_enemy(enemy)
                self._enemies_rereleased = True

class RoundEndState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        if  self.game.active_powerup:
            self.game.active_powerup.deactivate()
            self.game.active_powerup = None
        self._update_count = 0

    def update(self):
        for ball in self.game.balls:
            ball.speed = 0
            ball.visible = False
        self.game.paddle.visible = False
        for enemy in self.game.enemies:
            enemy.visible = False
        self.game.enemies.clear()
        self.game.round.edges.top.cancel_open_door()
        if  self._update_count > 120:
            self.game.balls = self.game.balls[:1]
            if  self.game.round.next_round is not None:
                self.game.round = self.game.round.next_round(TOP_OFFSET)
                self.game.state = RoundStartState(self.game)
            else:
                self.game.state = GameEndState(self.game)
        self._update_count += 1

class GameEndState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        game.ball.anchor(game.paddle.rect.midtop)
        game.ball.visible = False
        game.over = True
        receiver.unregister_handler(self.game.handler_move_left, self.game.handler_move_right, self.game.handler_stop)
        #---- kong ----
        receiver.unregister_handler(self.game.handler_quit)
        #----

    def update(self):
        pass

#
#
#
