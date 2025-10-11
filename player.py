import pygame
from os.path import join
from laser import Laser


class Player(pygame.sprite.Sprite):
    def __init__(self, groups, screen_width, screen_height, laser_surf, all_sprites, laser_sprites, laser_sound, player_id=1):
        super().__init__(groups)
        player_images = {
            1: 'player.png',
            2: 'player2.png',
            3: 'player3.png',
            4: 'player4.png'
        }
        image_name = player_images.get(player_id, 'player.png')
        self.og = pygame.image.load(join('images', image_name)).convert_alpha()
        self.image = self.og
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300

        self.laser_surf = laser_surf
        self.all_sprites = all_sprites
        self.laser_sprites = laser_sprites
        self.laser_sound = laser_sound

        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400  # 400ms entre disparos

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt, events):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN] - keys[pygame.K_UP])
        # Para que no aumente la velocidad cuando va en diagonal
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.can_shoot:
                Laser([self.all_sprites, self.laser_sprites], self.laser_surf, self.rect.midtop)
                self.can_shoot = False
                self.laser_shoot_time = pygame.time.get_ticks()
                self.laser_sound.play()

        self.laser_timer()
