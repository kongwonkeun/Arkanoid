#
#
#

import functools
import os
import pygame

HIGH_SCORE_FILE = os.path.join(os.path.expanduser('~'), '.arkanoid')

def load_png(filename):
    if  not filename.lower().endswith('.png'):
        filename = '{}.png'.format(filename)
    fullpath = os.path.join(os.path.dirname(__file__), '..', 'data', 'graphics', filename)
    if  not os.path.exists(fullpath):
        raise FileNotFoundError('file not found: {}'.format(fullpath))
    image = pygame.image.load(fullpath)
    if  image.get_alpha is None:
        image = image.convert()
    else:
        image = image.convert_alpha()
    return image, image.get_rect()

def load_png_sequence(filename_prefix):
    count, sequence = 1, []
    while True:
        filename = '%s_%s.png' % (filename_prefix, count)
        try:
            sequence.append(load_png(filename))
        except FileNotFoundError:
            break
        else:
            count += 1
    return sequence

@functools.lru_cache()
def font(name, size):
    return pygame.font.Font(os.path.join(os.path.dirname(__file__), '..', 'data', 'fonts', name), size)

def h_centre_pos(surface):
    screen = pygame.display.get_surface()
    return (screen.get_width() / 2) - (surface.get_width() / 2)

def save_high_score(value):
    with open(HIGH_SCORE_FILE, 'w') as file:
        file.write(str(value))

def load_high_score():
    if  not os.path.exists(HIGH_SCORE_FILE):
        return 0
    with open(HIGH_SCORE_FILE) as file:
        return int(file.read().strip())

#
#
#
