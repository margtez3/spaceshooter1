import pygame


class Laser(pygame.sprite.Sprite):
    def __init__(self, groups, surf, pos):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom=pos)
        self.speed = 400  # Velocidad del láser hacia arriba
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, events):
        self.rect.centery -= self.speed * dt

        if self.rect.bottom < 0:
            self.kill()
