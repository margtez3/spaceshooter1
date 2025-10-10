import pygame


class Laser(pygame.sprite.Sprite):
    """Clase para los láseres que dispara el jugador"""
    def __init__(self, groups, surf, pos):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom=pos)
        self.speed = 400  # Velocidad del láser hacia arriba
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, events):
        """Mueve el láser hacia arriba y lo elimina si sale de la pantalla"""
        self.rect.centery -= self.speed * dt

        # Eliminar el láser si sale de la pantalla por arriba
        if self.rect.bottom < 0:
            self.kill()
