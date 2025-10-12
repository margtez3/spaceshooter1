"""
Archivo con la clase Meteor.

Los meteoritos son los enemigos del juego que caen desde arriba
y deben ser esquivados o destruidos por el jugador.
"""

import pygame
from random import randint, uniform


class Meteor(pygame.sprite.Sprite):
    """
    Clase que representa un meteorito en el juego.

    Los meteoritos caen desde la parte superior de la pantalla con
    velocidad y dirección aleatorias, rotando mientras caen. Se destruyen
    automáticamente después de cierto tiempo o al salir de la pantalla.

    Atributos:
        og: Imagen original del meteorito
        image: Imagen actual rotada
        rect: Rectángulo para posición y colisiones
        start_time: Tiempo de cuando se creó el meteorito
        lifetime: Tiempo de vida en milisegundos
        direction: Vector de dirección del movimiento
        speed: Velocidad de caída en píxeles por segundo
        rotation_speed: Velocidad de rotación en grados por segundo
        rotation: Ángulo de rotación actual
    """

    def __init__(self, groups, surf, pos):
        """
        Inicializa un meteorito en la posición especificada.

        Argumentos:
            groups: Grupos de sprites a los que pertenece
            surf: Superficie con la imagen del meteorito
            pos: Tupla (x, y) con la posición inicial
        """
        super().__init__(groups)

        # Guardamos la imagen original para poder rotarla sin perder calidad
        self.og = surf
        self.image = surf
        self.rect = self.image.get_rect(center=pos)

        # Guardamos el tiempo de creación para calcular el lifetime
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000  # 3 segundos de vida

        # Dirección aleatoria
        # uniform genera un float aleatorio entre los valores dados
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1)

        # Velocidad aleatoria entre 500 y 600 píxeles por segundo
        self.speed = randint(500, 600)

        # Creamos una máscara para colisiones pixel-perfect
        # Esto permite detectar colisiones más precisas que solo con rectángulos
        self.mask = pygame.mask.from_surface(self.image)

        # Velocidad de rotación aleatoria
        self.rotation_speed = randint(50, 80)  # Grados por segundo
        self.rotation = 0  # Ángulo inicial

    def update(self, dt, events=None):
        """
        Actualiza la posición y rotación del meteorito cada frame.

        Argumentos:
            dt: Delta time en segundos
        """
        # Actualizamos la posición según la dirección y velocidad
        self.rect.center += self.direction * self.speed * dt

        # Verificamos si ya pasó el tiempo de vida
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()  # Eliminamos el sprite del juego

        # Actualizamos la rotación
        self.rotation += self.rotation_speed * dt

        # Rotamos la imagen original (no la ya rotada para evitar distorsión)
        # rotozoom permite rotar y escalar, usamos escala 1 para mantener tamaño
        self.image = pygame.transform.rotozoom(self.og, self.rotation, 1)

        # Actualizamos el rectángulo manteniendo el centro en la misma posición
        # (rotar cambia el tamaño del rectángulo)
        self.rect = self.image.get_rect(center=self.rect.center)
