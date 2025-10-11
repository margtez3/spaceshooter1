import pygame
from os.path import join
from laser import Laser


class Player(pygame.sprite.Sprite):
    def __init__(self, groups, screen_width, screen_height, laser_surf, all_sprites, laser_sprites, laser_sound,
                 player_number=1):
        super().__init__(groups)
        player_images = {
            1: 'player.png',
            2: 'player2.png',
            3: 'player3.png',
            4: 'player4.png'
        }

        image_file = player_images.get(player_number, 'player.png')
        self.og = pygame.image.load(join('images', image_file)).convert_alpha()
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

        self.lives = 3
        self.invulnerable = False
        self.hit_time = 0
        self.invulnerable_duration = 2000  # 2 segundos de invulnerabilidad después de ser golpeado

    def laser_timer(self):
        """Temporizador para controlar el cooldown entre disparos"""
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def invulnerability_timer(self):
        """Temporizador para la invulnerabilidad después de ser golpeado"""
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.hit_time >= self.invulnerable_duration:
                self.invulnerable = False

    def take_damage(self):
        """Reduce una vida del jugador"""
        if not self.invulnerable and self.lives > 0:
            self.lives -= 1
            self.invulnerable = True
            self.hit_time = pygame.time.get_ticks()
            return True
        return False

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
        self.invulnerability_timer()

        if self.invulnerable:
            # Parpadeo cada 100ms
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)
