import pygame
from os.path import join
from laser import Laser


class Player(pygame.sprite.Sprite):
    def __init__(self, groups, screen_width, screen_height, laser_surf, all_sprites, laser_sprites, laser_sound,
                 player_number=1):
        super().__init__(groups)
        # Imagen del jugador según el número (1 o 2)
        if player_number == 1:
            self.og = pygame.image.load(join('images', 'player.png')).convert_alpha()
        else:
            self.og = pygame.image.load(join('images', 'player2.png')).convert_alpha()

        self.image = self.og
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player_number = player_number

        # Referencias para disparar láseres
        self.laser_surf = laser_surf
        self.all_sprites = all_sprites
        self.laser_sprites = laser_sprites
        self.laser_sound = laser_sound

        # Control de disparo (cooldown)
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400  # 400ms entre disparos

    def laser_timer(self):
        """Temporizador para controlar el cooldown entre disparos"""
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt, events):
        """Actualiza la posición del jugador y maneja los disparos"""
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN] - keys[pygame.K_UP])

        # Normalizar dirección para que no aumente la velocidad en diagonal
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > self.screen_height:
            self.rect.bottom = self.screen_height

        # Manejar disparo con la barra espaciadora
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.can_shoot:
                Laser([self.all_sprites, self.laser_sprites], self.laser_surf, self.rect.midtop)
                self.can_shoot = False
                self.laser_shoot_time = pygame.time.get_ticks()
                self.laser_sound.play()

        self.laser_timer()
