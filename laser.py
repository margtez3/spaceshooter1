"""
Archivo con la clase Laser.

Los láseres son proyectiles que dispara el jugador para destruir meteoritos.
"""

import pygame


class Laser(pygame.sprite.Sprite):
    """
    Clase que representa un láser disparado por el jugador.

    Los láseres se mueven hacia arriba en línea recta y se destruyen
    al salir de la pantalla o al colisionar con un meteorito.

    Atributos:
        image: Superficie con la imagen del láser
        rect: Rectángulo para posición y colisiones
        speed: Velocidad de movimiento hacia arriba
        mask: Máscara de colisión pixel-perfect
    """

    def __init__(self, groups, surf, pos):
        """
        Inicializa un láser en la posición especificada.

        Argumentos:
            groups: Grupos de sprites a los que pertenece
            surf: Superficie con la imagen del láser
            pos: Tupla (x, y) con la posición inicial (con la nave)
        """
        super().__init__(groups)

        self.image = surf

        # Posicionamos el láser con su parte inferior en la posición dada

        self.rect = self.image.get_rect(midbottom=pos)

        self.speed = 400  # Velocidad en píxeles por segundo

        # Creamos una máscara para colisiones pixel-perfect
        # Esto permite detectar colisiones más precisas que solo con rectángulos
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, events):
        """
        Actualiza la posición del láser cada frame.

        Argumentos:
            dt: Delta time en segundos
            events: Lista de eventos

        Mueve el láser hacia arriba y lo destruye si sale de la pantalla.
        """
        # Movemos el láser hacia arriba
        self.rect.centery -= self.speed * dt

        # Si el láser salió completamente de la pantalla por arriba
        if self.rect.bottom < 0:
            self.kill()  # Lo eliminamos para liberar memoria
