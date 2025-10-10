import pygame
from random import randint

class Star(pygame.sprite.Sprite):
    """Clase para las estrellas del fondo"""
    def __init__(self, groups, surf, screen_width, screen_height):
        super().__init__(groups)
        self.image = surf
        # Posición aleatoria en la pantalla
        self.rect = self.image.get_rect(center=(randint(0, screen_width), randint(0, screen_height)))
