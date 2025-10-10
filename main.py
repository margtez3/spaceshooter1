"""
Versión single-player del juego Space Shooter
Para jugar multijugador, usa server.py y client.py
"""

import pygame
from os.path import join
from random import randint
from player import Player
from star import Star
from meteor import Meteor


class Explosion(pygame.sprite.Sprite):
    """Clase para las animaciones de explosión"""

    def __init__(self, frames, groups, pos):
        super().__init__(groups)
        self.frames = frames
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt, events=None):
        """Actualiza la animación de explosión"""
        self.index += 20 * dt
        if self.index < len(self.frames):
            self.image = self.frames[int(self.index)]
        else:
            self.kill()


class Button:
    """Clase para botones interactivos"""

    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = (180, 140, 255)
        self.hover_color = (255, 100, 150)
        self.text_color = (255, 255, 255)
        self.is_hovered = False

    def draw(self, screen):
        """Dibuja el botón en la pantalla"""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 3, border_radius=10)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        """Verifica si el mouse está sobre el botón"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        """Verifica si dio click """
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]


# Iniciamos pygame
pygame.init()

# Tamaños de la pantalla
W_WIDTH, W_HEIGHT = 1280, 800
screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()
running = True

GAME_STATE = "START"  # START, PLAYING, GAME_OVER

# Cargamos imágenes

laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

# Cargamos sonidos
laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
laser_sound.set_volume(0.5)
explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
explosion_sound.set_volume(0.4)
damage_sound = pygame.mixer.Sound(join('audio', 'damage.ogg'))
damage_sound.set_volume(0.6)
game_sound = pygame.mixer.Sound(join('audio', 'game_music.wav'))
game_sound.set_volume(0.4)
game_sound.play(loops=-1)

meteor_event = pygame.USEREVENT + 1
pygame.time.set_timer(meteor_event, 500)  # Generar meteoro cada 500ms

# Botones
start_button = Button(W_WIDTH // 2 - 100, W_HEIGHT // 2 + 50, 200, 60, "START", font)
restart_button = Button(W_WIDTH // 2 - 100, W_HEIGHT // 2 + 50, 200, 60, "RESTART", font)

# Grupos de sprites
star_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
player = None
game_start_time = 0
meteors_destroyed = 0


def init_game():
    """Inicializa o reinicia el juego"""
    global player, star_sprites, meteor_sprites, laser_sprites, all_sprites, game_start_time, meteors_destroyed

    # Limpiar todos los grupos de sprites
    star_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    all_sprites.empty()

    # Crear jugador
    player = Player(all_sprites, W_WIDTH, W_HEIGHT, laser_surf, all_sprites, laser_sprites, laser_sound)

    # Crear estrellas del fondo
    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    for i in range(20):
        Star(star_sprites, star_surf, W_WIDTH, W_HEIGHT)

    # Reiniciar el tiempo de inicio del juego
    game_start_time = pygame.time.get_ticks()
    meteors_destroyed = 0


def collisions():
    """Detecta y maneja las colisiones del juego"""
    global GAME_STATE, meteors_destroyed
    # Colisión entre jugador y meteoros
    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True)
    if collision_sprites:
        damage_sound.play()
        GAME_STATE = "GAME_OVER"

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if collided_sprites:
            laser.kill()
            Explosion(explosion_frames, all_sprites, laser.rect.midtop)
            explosion_sound.play()
            # Incrementar contador por cada meteoro destruido
            meteors_destroyed += len(collided_sprites)


def score():
    """Muestra el puntaje actual en pantalla"""
    text = font.render(f"Score: {meteors_destroyed}", True, (255, 255, 255))
    text_rect = text.get_rect(midbottom=(W_WIDTH / 2, W_HEIGHT - 50))
    pygame.draw.rect(screen, (255, 255, 255), text_rect.inflate(20, 30).move(0, -10), 5, 10)
    screen.blit(text, text_rect)


def draw_start_screen():
    """Dibuja la pantalla de inicio"""
    screen.fill('#3a2e3f')


    # Dibujar título
    title_text = title_font.render("SPACE SHOOTER", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 100))
    screen.blit(title_text, title_rect)

    # Dibujar subtítulo
    subtitle_text = font.render("¡Destruye los meteoros!", True, (200, 200, 200))
    subtitle_rect = subtitle_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 20))
    screen.blit(subtitle_text, subtitle_rect)

    # Dibujar botón
    start_button.draw(screen)


def draw_game_over_screen():
    """Dibuja la pantalla de game over"""
    screen.fill('#3a2e3f')


    # Dibujar texto de game over
    game_over_text = title_font.render("GAME OVER", True, (255, 50, 50))
    game_over_rect = game_over_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 100))
    screen.blit(game_over_text, game_over_rect)

    score_text = font.render(f"Score: {meteors_destroyed}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 20))
    screen.blit(score_text, score_rect)

    # Dibujar botón de reinicio
    restart_button.draw(screen)


# Loop principal del juego
while running:
    dt = clock.tick(60) / 1000  # Delta time en segundos
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    # Procesar eventos
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == meteor_event and GAME_STATE == "PLAYING":
            # Generar meteoro en posición aleatoria
            x = randint(0, W_WIDTH)
            y = randint(-200, -100)
            Meteor([all_sprites, meteor_sprites], meteor_surf, (x, y))

    # Máquina de estados del juego
    if GAME_STATE == "START":
        start_button.check_hover(mouse_pos)
        if start_button.is_clicked(mouse_pos, mouse_pressed):
            init_game()
            GAME_STATE = "PLAYING"

        draw_start_screen()

    elif GAME_STATE == "PLAYING":
        # Actualizar sprites
        star_sprites.update(dt, events)
        all_sprites.update(dt, events)
        collisions()

        # Dibujar en la pantalla
        screen.fill('#3a2e3f')

        score()
        star_sprites.draw(screen)
        all_sprites.draw(screen)

    elif GAME_STATE == "GAME_OVER":
        restart_button.check_hover(mouse_pos)
        if restart_button.is_clicked(mouse_pos, mouse_pressed):
            init_game()
            GAME_STATE = "PLAYING"

        draw_game_over_screen()

    pygame.display.update()

pygame.quit()
