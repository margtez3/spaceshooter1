"""
Cliente multijugador para Space Shooter - Hasta 4 jugadores
Ejecuta server.py primero, luego ejecuta este archivo
"""

import pygame
from os.path import join
from random import randint
import threading
from player import Player
from star import Star
from meteor import Meteor
from laser import Laser
from network import Network


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
        """Verifica si dio click"""
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
        label_surf = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 35))

        pygame.draw.rect(screen, self.color, self.rect, 3, border_radius=5)

        text_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))


# Iniciamos pygame
pygame.init()

# Tamaños de la pantalla
W_WIDTH, W_HEIGHT = 1280, 800
screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
pygame.display.set_caption("Space Shooter - Multijugador (4 Jugadores)")
clock = pygame.time.Clock()
running = True

GAME_STATE = "START"  # START, LOGIN, INSTRUCTIONS, CONNECTING, WAITING, PLAYING, GAME_OVER

# Network
network = Network()
player_id = None
game_data = None
data_lock = threading.Lock()
username = ""

# Cargamos imágenes
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
life_surf = pygame.image.load(join('images', 'life.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 30)
title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 25)
input_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 25)
tiny_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 20)
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

username_input = InputBox(W_WIDTH // 2 - 200, 250, 400, 50, input_font, "Nombre:", "Jugador1")
ip_input = InputBox(W_WIDTH // 2 - 200, 350, 400, 50, input_font, "IP del Servidor:", "127.0.0.1")
port_input = InputBox(W_WIDTH // 2 - 200, 450, 400, 50, input_font, "Puerto:", "5555")
connect_button = Button(W_WIDTH // 2 - 100, 550, 200, 60, "CONECTAR", font)

# Botones
start_button = Button(W_WIDTH // 2 - 100, W_HEIGHT // 2 + 100, 200, 60, "JUGAR", font)
instructions_button = Button(W_WIDTH // 2 - 150, W_HEIGHT // 2 + 180, 300, 60, "INSTRUCCIONES", font)
back_button = Button(50, 50, 150, 50, "VOLVER", small_font)
restart_button = Button(W_WIDTH // 2 - 100, W_HEIGHT - 150, 200, 60, "REINICIAR", font)

# Sprites
star_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
other_players_group = pygame.sprite.Group()
explosion_sprites = pygame.sprite.Group()

player = None
other_players = {}
last_laser_count = 0
last_lives = 3
processed_meteors = set()


def connect_to_server(ip, port):
    """Conecta al servidor usando el módulo network"""
    global player_id, GAME_STATE, username

    success, result = network.connect(ip, port)

    if success:
        player_id = result
        if network.send_name(username):
            print(f"[CONECTADO] Eres el Jugador {player_id}")
            GAME_STATE = "WAITING"
        else:
            print("[ERROR] No se pudo enviar el nombre")
            network.last_error = "Error al enviar nombre al servidor"
            GAME_STATE = "ERROR"
    else:
        print(f"[ERROR] {result}")
        network.last_error = result
        GAME_STATE = "ERROR"


def receive_game_state():
    """Hilo que recibe constantemente el estado del juego del servidor"""
    global game_data, running, GAME_STATE, last_lives

    while running and network.connected:
        try:
            # Enviar un mensaje vacío para mantener la conexión y recibir actualizaciones
            response = network.send({'type': 'heartbeat'})

            if response:
                with data_lock:
                    game_data = response

                    if game_data.get('game_started') and GAME_STATE == "WAITING":
                        GAME_STATE = "PLAYING"

                    if game_data and 'players' in game_data:
                        if player_id in game_data['players']:
                            current_lives = game_data['players'][player_id].get('lives', 3)
                            if current_lives < last_lives:
                                damage_sound.play()
                            last_lives = current_lives

                            # Check if player is out of the game
                            if current_lives <= 0 and GAME_STATE == "PLAYING":
                                GAME_STATE = "GAME_OVER"
        except Exception as e:
            print(f"[ERROR] Error recibiendo datos: {e}")
            break


def init_game():
    """Inicializa el juego"""
    global player, star_sprites, meteor_sprites, laser_sprites, all_sprites
    global other_players, last_laser_count, explosion_sprites, last_lives, processed_meteors

    # Limpiamos los sprites
    star_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    all_sprites.empty()
    other_players_group.empty()
    explosion_sprites.empty()
    other_players = {}
    processed_meteors = set()

    # Creamos las estrellas del fondo
    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    for i in range(20):
        Star(star_sprites, star_surf, W_WIDTH, W_HEIGHT)

    # Creamos el jugador local
    player = Player(all_sprites, W_WIDTH, W_HEIGHT, laser_surf, all_sprites, laser_sprites, laser_sound, player_id)
    last_laser_count = 0
    last_lives = 3



    # Notificar al servidor que el juego comenzó
    network.send({'type': 'start_game'})

    # Iniciar hilo de recepción
    if not any(t.name == "receive_thread" for t in threading.enumerate()):
        receive_thread = threading.Thread(target=receive_game_state, daemon=True, name="receive_thread")
        receive_thread.start()


def update_from_server():
    """Actualiza el estado local basado en los datos del servidor"""
    global other_players, game_data

    if game_data is None:
        return

    with data_lock:
        current_player_ids = set()
        for pid, pdata in game_data['players'].items():
            if pid != player_id:
                current_player_ids.add(pid)

                # Crear o actualizar sprite del otro jugador
                if pid not in other_players:
                    other_players[pid] = Player(other_players_group, W_WIDTH, W_HEIGHT, laser_surf,
                                                other_players_group, pygame.sprite.Group(), laser_sound, pid)

                other_players[pid].rect.centerx = pdata['x']
                other_players[pid].rect.centery = pdata['y']
                other_players[pid].lives = pdata.get('lives', 3)

        # Eliminar jugadores desconectados
        for pid in list(other_players.keys()):
            if pid not in current_player_ids:
                other_players[pid].kill()
                del other_players[pid]

        # Actualizar meteoros
        meteor_sprites.empty()
        for meteor_data in game_data['meteors']:
            meteor = Meteor([meteor_sprites], meteor_surf, (meteor_data['x'], meteor_data['y']))
            meteor.rotation = meteor_data['rotation']
            meteor.meteor_id = meteor_data['id']

        # Actualizar láseres
        laser_sprites.empty()
        for laser_data in game_data.get('lasers', []):
            laser = Laser([laser_sprites], laser_surf, (laser_data['x'], laser_data['y']))


def check_collisions():
    """Verifica colisiones entre el jugador y los meteoros"""
    global player, processed_meteors

    if player and player.lives > 0:
        # Verificar colisión con meteoros
        for meteor in meteor_sprites:
            if hasattr(meteor, 'meteor_id') and meteor.meteor_id in processed_meteors:
                continue

            dx = meteor.rect.centerx - player.rect.centerx
            dy = meteor.rect.centery - player.rect.centery
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < 50:  # Radio de colisión
                if player.take_damage():
                    if hasattr(meteor, 'meteor_id'):
                        processed_meteors.add(meteor.meteor_id)
                    # Actualizar vidas en el servidor
                    network.send({'type': 'update_lives', 'lives': player.lives})


def draw_ui():
    """Dibuja la interfaz de usuario con vidas y puntajes"""
    if game_data and 'players' in game_data:
        y_offset = 20

        for pid in sorted(game_data['players'].keys()):
            pdata = game_data['players'][pid]
            name = pdata.get('name', f'Jugador {pid}')
            score = pdata.get('score', 0)
            lives = pdata.get('lives', 0)

            color = (200, 150, 255) if pid == player_id else (255, 255, 255)

            # Nombre y puntaje
            text = small_font.render(f"{name}: {score}", True, color)
            screen.blit(text, (20, y_offset))

            # Vidas (corazones)
            for i in range(lives):
                screen.blit(life_surf, (20 + i * 35, y_offset + 35))

            y_offset += 90


def draw_start_screen():
    """Dibuja la pantalla de inicio"""
    screen.fill('#3a2e3f')

    title_text = title_font.render("SPACE-SHOOTER", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 150))
    screen.blit(title_text, title_rect)

    subtitle_text = small_font.render("MULTIJUGADOR - 4 JUGADORES", True, (200, 150, 255))
    subtitle_rect = subtitle_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 70))
    screen.blit(subtitle_text, subtitle_rect)

    start_button.draw(screen)
    instructions_button.draw(screen)


def draw_login_screen():
    """Dibuja la pantalla de login/conexión"""
    screen.fill('#3a2e3f')

    title_text = title_font.render("CONECTAR", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(W_WIDTH // 2, 120))
    screen.blit(title_text, title_rect)

    username_input.draw(screen)
    ip_input.draw(screen)
    port_input.draw(screen)
    connect_button.draw(screen)

    back_button.draw(screen)


def draw_instructions_screen():
    """Dibuja la pantalla de instrucciones"""
    screen.fill('#3a2e3f')

    title_text = title_font.render("INSTRUCCIONES", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(W_WIDTH // 2, 100))
    screen.blit(title_text, title_rect)

    instructions = [
        "CONTROLES:",
        "• Flechas: ← ↑↓ → ",
        "• Espacio: Disparar",
        "",
        "OBJETIVO:",
        "• Destruye la mayor cantidad de meteoritos posibles",
        "• Evita ser golpeado por meteoros",
        "• Cada jugador tiene 3 vidas",
        "• Pierdes una vida al chocar con un meteoro",
        "• El jugador con más puntos gana",
        "",
        "¡ Buena suerte ;) !"
    ]

    y_offset = 220
    for line in instructions:
        if line.startswith("•"):
            text = small_font.render(line, True, (200, 200, 200))
        elif line == "":
            y_offset += 10
            continue
        else:
            text = font.render(line, True, (255, 255, 100))

        text_rect = text.get_rect(center=(W_WIDTH // 2, y_offset))
        screen.blit(text, text_rect)
        y_offset += 45

    back_button.draw(screen)


def draw_connecting_screen():
    """Dibuja la pantalla de conexión"""
    screen.fill('#3a2e3f')

    connecting_text = title_font.render("CONECTANDO...", True, (255, 255, 255))
    connecting_rect = connecting_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2))
    screen.blit(connecting_text, connecting_rect)


def draw_waiting_screen():
    """Dibuja la pantalla de espera para que el servidor inicie el juego"""
    screen.fill('#3a2e3f')

    waiting_text = title_font.render("ESPERANDO...", True, (255, 255, 255))
    waiting_rect = waiting_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 - 50))
    screen.blit(waiting_text, waiting_rect)

    info_text = small_font.render("Esperando a que se conecten más jugadores", True, (200, 200, 200))
    info_rect = info_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 + 20))
    screen.blit(info_text, info_rect)

    if game_data and 'players' in game_data:
        players_text = small_font.render(f"Jugadores conectados: {len(game_data['players'])}/4", True, (200, 150, 255))
        players_rect = players_text.get_rect(center=(W_WIDTH // 2, W_HEIGHT // 2 + 70))
        screen.blit(players_text, players_rect)


def draw_game_over_screen():
    """Dibuja la pantalla de game over con tabla de resultados"""
    screen.fill('#3a2e3f')

    game_over_text = title_font.render("GAME OVER", True, (255, 50, 50))
    game_over_rect = game_over_text.get_rect(center=(W_WIDTH // 2, 100))
    screen.blit(game_over_text, game_over_rect)

    if game_data and 'players' in game_data:
        leaderboard_text = font.render("TABLA DE RESULTADOS", True, (255, 255, 100))
        leaderboard_rect = leaderboard_text.get_rect(center=(W_WIDTH // 2, 200))
        screen.blit(leaderboard_text, leaderboard_rect)

        # Ordenar jugadores por puntaje (mayor a menor)
        sorted_players = sorted(
            game_data['players'].items(),
            key=lambda x: x[1].get('score', 0),
            reverse=True
        )

        y_offset = 280
        for rank, (pid, pdata) in enumerate(sorted_players, 1):
            name = pdata.get('name', f'Jugador {pid}')
            score = pdata.get('score', 0)

            if rank == 1:
                color = (255, 215, 0)  # Dorado
                medal = "🏆"
            elif rank == 2:
                color = (192, 192, 192)  # Plateado
                medal = "🥈"
            elif rank == 3:
                color = (205, 127, 50)  # Bronce
                medal = "🥉"
            else:
                color = (200, 200, 200)
                medal = ""

            if pid == player_id:
                pygame.draw.rect(screen, (150, 100, 200),
                                 pygame.Rect(W_WIDTH // 2 - 250, y_offset - 10, 500, 50),
                                 border_radius=10)

            rank_text = small_font.render(f"{rank}. {name}: {score} puntos {medal}", True, color)
            rank_rect = rank_text.get_rect(center=(W_WIDTH // 2, y_offset + 10))
            screen.blit(rank_text, rank_rect)

            y_offset += 60

    restart_button.draw(screen)


# Loop principal del juego
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
            GAME_STATE = "START"

    if GAME_STATE == "START":
        start_button.check_hover(mouse_pos)
        instructions_button.check_hover(mouse_pos)

        if start_button.is_clicked(mouse_pos, mouse_pressed):
            GAME_STATE = "LOGIN"
        elif instructions_button.is_clicked(mouse_pos, mouse_pressed):
            GAME_STATE = "INSTRUCTIONS"

        draw_start_screen()

    elif GAME_STATE == "INSTRUCTIONS":
        back_button.check_hover(mouse_pos)

        if back_button.is_clicked(mouse_pos, mouse_pressed):
            GAME_STATE = "START"

        draw_instructions_screen()

    elif GAME_STATE == "LOGIN":
        connect_button.check_hover(mouse_pos)
        back_button.check_hover(mouse_pos)

        if connect_button.is_clicked(mouse_pos, mouse_pressed):
            username = username_input.text if username_input.text else "Jugador"
            server_ip = ip_input.text if ip_input.text else "127.0.0.1"
            server_port = port_input.text if port_input.text else "5555"
            GAME_STATE = "CONNECTING"

            connect_thread = threading.Thread(
                target=lambda: connect_to_server(server_ip, server_port),
                daemon=True
            )
            connect_thread.start()
        elif back_button.is_clicked(mouse_pos, mouse_pressed):
            GAME_STATE = "START"

        draw_login_screen()

    elif GAME_STATE == "CONNECTING":
        draw_connecting_screen()

    elif GAME_STATE == "ERROR":
            draw_error_screen()

    elif GAME_STATE == "WAITING":
        if player is None:
            init_game()

        update_from_server()

        draw_waiting_screen()

    elif GAME_STATE == "PLAYING":
        if player is None:
            init_game()

        # Actualizar sprites locales
        star_sprites.update(dt, events)
        all_sprites.update(dt, events)
        explosion_sprites.update(dt, events)

        # Enviar disparos al servidor
        current_laser_count = len(laser_sprites)
        if current_laser_count > last_laser_count:
            for laser in laser_sprites:
                network.send({
                    'type': 'shoot_laser',
                    'x': laser.rect.centerx,
                    'y': laser.rect.centery
                })
            last_laser_count = current_laser_count
        else:
            last_laser_count = current_laser_count

        # Enviar posición del jugador al servidor
        network.send({
            'type': 'update_position',
            'x': player.rect.centerx,
            'y': player.rect.centery
        })

        # Actualizar desde el servidor
        update_from_server()

        # Verificar colisiones locales
        check_collisions()

        # Dibujar todo
        screen.fill('#3a2e3f')
        star_sprites.draw(screen)
        meteor_sprites.draw(screen)
        all_sprites.draw(screen)
        other_players_group.draw(screen)
        explosion_sprites.draw(screen)
        draw_ui()

    elif GAME_STATE == "GAME_OVER":
        restart_button.check_hover(mouse_pos)

        if restart_button.is_clicked(mouse_pos, mouse_pressed):
            network.disconnect()
            player = None
            game_data = None
            processed_meteors = set()
            GAME_STATE = "START"

        draw_game_over_screen()

    pygame.display.update()

# Cerrar conexión
network.disconnect()
pygame.quit()

