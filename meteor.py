import pygame
from random import randint, uniform


class Meteor(pygame.sprite.Sprite):
    """Clase para los meteoros que caen del cielo"""
    def __init__(self, groups, surf, pos):
        super().__init__(groups)
        self.og = surf
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000  # Tiempo de vida en milisegundos
        # Dirección con un poco de movimiento horizontal aleatorio
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation_speed = randint(50, 80)  # Velocidad de rotación
        self.rotation = 0

    def update(self, dt, events=None):
        """Actualiza la posición y rotación del meteoro"""
        # Mover el meteoro
        self.rect.center += self.direction * self.speed * dt

        # Eliminar el meteoro después de su tiempo de vida
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

        # Rotar el meteoro para efecto visual
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.og, self.rotation, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
