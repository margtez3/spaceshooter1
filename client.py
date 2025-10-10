"""
Cliente multijugador para Space Shooter
Ejecuta este archivo después de iniciar el servidor

"""

import pygame
from os.path import join
from random import randint
import socket
import pickle
import threading
from player import Player
from star import Star
from meteor import Meteor
from laser import Laser


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
        """Verifica si dieron click """
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]


class InputBox:
    """Clase para campos de entrada de texto"""

    def __init__(self, x, y, width, height, font, label, default_text=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = (100, 100, 100)
        self.color_active = (180, 140, 255)
        self.color = self.color_inactive
        self.font = font
        self.label = label
        self.text = default_text
        self.active = False

    def handle_event(self, event):
        """Maneja eventos de teclado y mouse"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Si el usuario hace clic en el input box
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
                self.color = self.color_inactive
            else:
                self.text += event.unicode

    def draw(self, screen):
        """Dibuja el campo de entrada"""
        # Dibujar label
        label_surf = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 35))

        # Dibujar caja
        pygame.draw.rect(screen, self.color, self.rect, 3, border_radius=5)

        # Dibujar texto
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))


# Iniciamos pygame
pygame.init()

# Tamaños de la pantalla
W_WIDTH, W_HEIGHT = 1280, 800
screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
pygame.display.set_caption("Space Shooter - Multijugador")
clock = pygame.time.Clock()
running = True

GAME_STATE = "LOGIN"  # LOGIN, CONNECTING, START, PLAYING, GAME_OVER
player_id = None
game_data = None
data_lock = threading.Lock()
username = ""
server_ip = ""
server_port = ""

# Cargamos imágenes
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 30)
input_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 25)
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

username_input = InputBox(W_WIDTH // 2 - 200, 250, 400, 50, input_font, "Username:", "Jugador1")
ip_input = InputBox(W_WIDTH // 2 - 200, 350, 400, 50, input_font, "IP del Servidor:", "localhost")
port_input = InputBox(W_WIDTH // 2 - 200, 450, 400, 50, input_font, "Puerto:", "5555")
connect_button = Button(W_WIDTH // 2 - 100, 550, 200, 60, "CONECTAR", font)

# Botones
start_button = Button(W_WIDTH // 2 - 100, W_HEIGHT // 2 + 50, 200, 60, "START", font)
restart_button = Button(W_WIDTH // 2 - 100, W_HEIGHT // 2 + 50, 200, 60, "RESTART", font)

# Sprites
star_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
other_players_group = pygame.sprite.Group()
explosion_sprites = pygame.sprite.Group()

player = None
other_player = None
game_start_time = 0
client_socket = None
last_laser_count = 0


def connect_to_server(ip, port):
    """Conecta al servidor y recibe el ID del jugador"""
    global client_socket, player_id, GAME_STATE

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, int(port)))

        # Recibir ID del jugador
        data = client_socket.recv(4096)
        message = pickle.loads(data)

        if message['type'] == 'player_id':
            player_id = message['id']
            print(f"[CONECTADO] Eres el Jugador {player_id}")
            GAME_STATE = "START"
            return True
        elif message['type'] == 'error':
            print(f"[ERROR] {message['message']}")
            GAME_STATE = "ERROR"
            return False
    except Exception as e:
        print(f"[ERROR] No se pudo conectar al servidor: {e}")
        GAME_STATE = "ERROR"
        return False


def receive_game_state():
    """Hilo que recibe constantemente el estado del juego del servidor"""
    global game_data, running, GAME_STATE

    while running:
        try:
            data = client_socket.recv(8192)
            if not data:
                break

            with data_lock:
                game_data = pickle.loads(data)

                if game_data and 'players' in game_data:
                    if player_id in game_data['players']:
                        if not game_data['players'][player_id].get('alive', True):
                            if GAME_STATE == "PLAYING":
                                damage_sound.play()
                                GAME_STATE = "GAME_OVER"
        except Exception as e:
            print(f"[ERROR] Error recibiendo datos: {e}")
            break


def send_to_server(message):
    """Envía un mensaje al servidor"""
    try:
        client_socket.send(pickle.dumps(message))
    except Exception as e:
        print(f"[ERROR] Error enviando datos: {e}")


def init_game():
    """Inicializa el juego"""
    global player, star_sprites, meteor_sprites, laser_sprites, all_sprites, game_start_time, other_player, last_laser_count, explosion_sprites

    # Limpiamos los sprites
    star_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    all_sprites.empty()
    other_players_group.empty()
    explosion_sprites.empty()

    # Creamos el jugador local
    player = Player(all_sprites, W_WIDTH, W_HEIGHT, laser_surf, all_sprites, laser_sprites, laser_sound, player_id)
    last_laser_count = 0

    # Creamos las estrellas del fondo
    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    for i in range(20):
        Star(star_sprites, star_surf, W_WIDTH, W_HEIGHT)

    # Reset del tiempo de inicio
    game_start_time = pygame.time.get_ticks()

    # Notificar al servidor que el juego comenzó
    send_to_server({'type': 'start_game'})


def update_from_server():
    """Actualiza el estado local basado en los datos del servidor"""
    global other_player, game_data, last_laser_count

    if game_data is None:
        return

    with data_lock:
        # Actualizar otros jugadores
        for pid, pdata in game_data['players'].items():
            if pid != player_id:
                # Crear o actualizar sprite del otro jugador
                if other_player is None:
                    player2_surf = pygame.image.load(join('images', 'player2.png')).convert_alpha()
                    other_player = Player(other_players_group, W_WIDTH, W_HEIGHT, laser_surf,
                                          other_players_group, pygame.sprite.Group(), laser_sound, pid)
                    other_player.image = player2_surf

                other_player.rect.centerx = pdata['x']
                other_player.rect.centery = pdata['y']

        # Actualizar meteoros
        meteor_sprites.empty()
        for meteor_data in game_data['meteors']:
            meteor = Meteor([meteor_sprites], meteor_surf, (meteor_data['x'], meteor_data['y']))
            meteor.rotation = meteor_data['rotation']

        laser_sprites.empty()
        for laser_data in game_data.get('lasers', []):
            laser = Laser(laser_surf, (laser_data['x'], laser_data['y']), [laser_sprites])


def score():
    """Muestra el puntaje en pantalla"""
    if game_data and 'scores' in game_data:
        # Puntaje del jugador local
        my_score = game_data['scores'].get(player_id, 0)
        text = font.render(f"{username}: {my_score}", True, (100, 255, 100))
        text_rect = text.get_rect(midtop=(W_WIDTH / 2, 20))
        pygame.draw.rect(screen, (255, 255, 255), text_rect.inflate(20, 20), 3, 10)
        screen.blit(text, text_rect)

        # Puntajes de otros jugadores
        y_offset = 70
        for pid, score_value in game_data['scores'].items():
            if pid != player_id:
                other_text = small_font.render(f"Jugador {pid}: {score_value}", True, (255, 200, 100))
                other_rect = other_text.get_rect(midtop=(W_WIDTH / 2, y_offset))
                screen.blit(other_text, other_rect)
                y_offset += 40


def draw_login_screen():
    """Dibuja la pantalla de login"""
    screen.fill('#3a2e3f')

    # Título
    title_text = title_font.render("SPACE SHOOTER", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(W_WIDTH // 2, 120))
    screen.blit(title_text, title_rect)

    # Subtítulo
    subtitle_text = small_font.render("MULTIJUGADOR", True, (100, 255, 100))
    subtitle_rect = subtitle_text.get_rect(center=(W_WIDTH // 2, 180))
    screen.blit(subtitle_text, subtitle_rect)

    # Campos de entrada
    username_input.draw(screen)
    ip_input.draw(screen)
    port_input.draw(screen)

    # Botón de conectar
    connect_button.draw(screen)


def draw_start_screen():
    """Dibuja la pantalla de inicio"""
    screen.fill('#3a2e3f')

    # Título
    title_text = title_font.render("SPACE SHOOTER", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 150))
    screen.blit(title_text, title_rect)

    # Subtítulo
    subtitle_text = font.render("MULTIJUGADOR", True, (100, 255, 100))
    subtitle_rect = subtitle_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 80))
    screen.blit(subtitle_text, subtitle_rect)

    # Info del jugador
    player_text = small_font.render(f"{username} - Jugador {player_id}", True, (200, 200, 200))
    player_rect = player_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 20))
    screen.blit(player_text, player_rect)

    # Botón
    start_button.draw(screen)


def draw_game_over_screen():
    """Dibuja la pantalla de game over"""
    screen.fill('#3a2e3f')

    # Texto de game over
    game_over_text = title_font.render("GAME OVER", True, (255, 50, 50))
    game_over_rect = game_over_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 150))
    screen.blit(game_over_text, game_over_rect)

    if game_data and 'scores' in game_data:
        my_score = game_data['scores'].get(player_id, 0)
        score_text = font.render(f"{username}: {my_score} meteoros", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 60))
        screen.blit(score_text, score_rect)

        # Mostrar puntaje del otro jugador
        y_offset = W_HEIGHT // 2 - 10
        for pid, score_value in game_data['scores'].items():
            if pid != player_id:
                other_text = small_font.render(f"Jugador {pid}: {score_value} meteoros", True, (200, 200, 200))
                other_rect = other_text.get_rect(center=(W_WIDTH // 2, y_offset))
                screen.blit(other_text, other_rect)
                y_offset += 40

    # Botón de reinicio
    restart_button.draw(screen)


def draw_connecting_screen():
    """Dibuja la pantalla de conexión"""
    screen.fill('#3a2e3f')

    connecting_text = title_font.render("CONECTANDO...", True, (255, 255, 255))
    connecting_rect = connecting_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2))
    screen.blit(connecting_text, connecting_rect)


def draw_error_screen():
    """Dibuja la pantalla de error"""
    screen.fill('#3a2e3f')

    error_text = title_font.render("ERROR", True, (255, 50, 50))
    error_rect = error_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 50))
    screen.blit(error_text, error_rect)

    msg_text = font.render("No se pudo conectar al servidor", True, (255, 255, 255))
    msg_rect = msg_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 + 20))
    screen.blit(msg_text, msg_rect)

    back_text = small_font.render("Presiona ESC para volver", True, (200, 200, 200))
    back_rect = back_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 + 80))
    screen.blit(back_text, back_rect)


# Loop principal
while running:
    dt = clock.tick(60) / 1000
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

        if GAME_STATE == "LOGIN":
            username_input.handle_event(event)
            ip_input.handle_event(event)
            port_input.handle_event(event)

        if GAME_STATE == "ERROR" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            GAME_STATE = "LOGIN"

    if GAME_STATE == "LOGIN":
        connect_button.check_hover(mouse_pos)
        if connect_button.is_clicked(mouse_pos, mouse_pressed):
            username = username_input.text if username_input.text else "Jugador"
            server_ip = ip_input.text if ip_input.text else "localhost"
            server_port = port_input.text if port_input.text else "5555"
            GAME_STATE = "CONNECTING"
            # Conectar al servidor en un hilo separado
            connect_thread = threading.Thread(target=lambda: connect_to_server(server_ip, server_port), daemon=True)
            connect_thread.start()

        draw_login_screen()

    elif GAME_STATE == "CONNECTING":
        draw_connecting_screen()

    elif GAME_STATE == "ERROR":
        draw_error_screen()

    elif GAME_STATE == "START":
        if client_socket and not any(t.name == "receive_thread" for t in threading.enumerate()):
            receive_thread = threading.Thread(target=receive_game_state, daemon=True, name="receive_thread")
            receive_thread.start()

        start_button.check_hover(mouse_pos)
        if start_button.is_clicked(mouse_pos, mouse_pressed):
            init_game()
            GAME_STATE = "PLAYING"

        draw_start_screen()

    elif GAME_STATE == "PLAYING":
        # Actualizar sprites locales
        star_sprites.update(dt, events)
        all_sprites.update(dt, events)
        explosion_sprites.update(dt, events)

        current_laser_count = len(laser_sprites)
        if current_laser_count > last_laser_count:
            # Se disparó un nuevo láser
            for laser in laser_sprites:
                send_to_server({
                    'type': 'shoot_laser',
                    'x': laser.rect.centerx,
                    'y': laser.rect.centery
                })
            last_laser_count = current_laser_count
        else:
            last_laser_count = current_laser_count

        # Enviar posición del jugador al servidor
        send_to_server({
            'type': 'update_position',
            'x': player.rect.centerx,
            'y': player.rect.centery
        })

        # Actualizar desde el servidor
        update_from_server()

        # Dibujar todo
        screen.fill('#3a2e3f')
        score()
        star_sprites.draw(screen)
        all_sprites.draw(screen)
        other_players_group.draw(screen)
        meteor_sprites.draw(screen)
        explosion_sprites.draw(screen)

    elif GAME_STATE == "GAME_OVER":
        restart_button.check_hover(mouse_pos)
        if restart_button.is_clicked(mouse_pos, mouse_pressed):
            init_game()
            GAME_STATE = "PLAYING"

        draw_game_over_screen()

    pygame.display.update()

# Cerrar conexión
if client_socket:
    client_socket.close()

pygame.quit()
