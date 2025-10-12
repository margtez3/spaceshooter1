"""
Archivo con la clase Star.

Las estrellas son elementos decorativos que se muestran en el fondo
para dar sensación de movimiento y profundidad espacial.
"""

import pygame
from random import randint


class Star(pygame.sprite.Sprite):
    """
    Clase que representa una estrella en el fondo del juego.

    Las estrellas son sprites estáticos que se colocan aleatoriamente
    en la pantalla para crear un efecto de espacio exterior.

    Atributos:
        image: Superficie de pygame con la imagen de la estrella
        rect: Rectángulo que define la posición y tamaño de la estrella
    """

    def __init__(self, groups, surf, screen_width, screen_height):
        """
        Inicializa una estrella en una posición aleatoria.

        Argumentos:
            groups: Grupos de sprites a los que pertenece esta estrella
            surf: Superficie de pygame con la imagen de la estrella
            screen_width: Ancho de la pantalla en píxeles
            screen_height: Alto de la pantalla en píxeles
        """
        # Llamamos al constructor de la clase padre (Sprite)
        super().__init__(groups)

        # Guardamos la imagen de la estrella
        self.image = surf

        # Creamos el rectángulo y lo posicionamos aleatoriamente
        # randint genera un número entero aleatorio entre 0 y el tamaño de pantalla
        self.rect = self.image.get_rect(
            center=(randint(0, screen_width), randint(0, screen_height))
        )
