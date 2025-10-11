import pygame
from os.path import join
from random import randint
from player import Player
from star import Star
from meteor import Meteor
from network import Network


class Explosion(pygame.sprite.Sprite):
    def __init__(self, frames, groups, pos):
        super().__init__(groups)
        self.frames = frames
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt, events=None):
        self.index += 20 * dt
        if self.index < len(self.frames):
            self.image = self.frames[int(self.index)]
        else:
            self.kill()


class Button:
    def __init__(self, x, y, width, height, text, font, color=(180, 140, 255), hover_color=(255, 100, 150)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = (255, 255, 255)
        self.is_hovered = False

    def draw(self, screen):
        """Dibuja el botón con efecto de sombra"""
        color = self.hover_color if self.is_hovered else self.color

        # Sombra del botón
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)

        # Botón principal
        pygame.draw.rect(screen, color, self.rect, border_radius=15)

        # Borde brillante
        border_color = (255, 255, 255) if self.is_hovered else (200, 200, 200)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=15)

        # Texto
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        """Verifica si el mouse está sobre el botón"""
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        """Verifica si el botón fue clickeado"""
        return self.rect.collidepoint(pos)


class InputBox:
    """Clase para campos de entrada de texto"""

    def __init__(self, x, y, width, height, font, label, default_text=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = (60, 70, 100)
        self.color_active = (80, 140, 220)
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
        """Dibuja el campo de entrada con diseño mejorado"""
        # Label
        label_surf = self.font.render(self.label, True, (200, 220, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 35))

        # Fondo del input con sombra interior
        background_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(screen, (20, 25, 40), background_rect, border_radius=8)

        # Borde del input
        border_color = self.color if self.active else (100, 110, 140)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=8)

        # Texto
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (self.rect.x + 15, self.rect.y + 12))

        # Cursor parpadeante si está activo
        if self.active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = self.rect.x + 15 + text_surf.get_width() + 2
            pygame.draw.line(screen, (255, 255, 255),
                             (cursor_x, self.rect.y + 10),
                             (cursor_x, self.rect.y + self.rect.height - 10), 2)


def draw_gradient_background(screen, color1, color2):
    """Dibuja un fondo con gradiente vertical"""
    height = screen.get_height()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


def draw_panel(screen, rect, color=(30, 35, 55), alpha=220):
    """Dibuja un panel decorativo con sombra"""
    # Sombra
    shadow_rect = rect.copy()
    shadow_rect.inflate_ip(8, 8)
    shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(), border_radius=20)
    screen.blit(shadow_surf, shadow_rect)

    # Panel principal
    panel_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (*color, alpha), panel_surf.get_rect(), border_radius=20)
    screen.blit(panel_surf, rect)

    # Borde brillante
    pygame.draw.rect(screen, (100, 120, 180, 150), rect, 2, border_radius=20)


def show_login_screen(screen, font):
    """Muestra la pantalla de login mejorada"""
    clock = pygame.time.Clock()

    username_input = InputBox(325, 260, 350, 55, font, "Username:", "Player1")
    ip_input = InputBox(325, 360, 350, 55, font, "Server IP:", "127.0.0.1")
    port_input = InputBox(325, 460, 350, 55, font, "Port:", "5555")

    start_button = Button(280, 580, 230, 80, "Start", font,
                          color=(60, 180, 120), hover_color=(80, 220, 150))
    instructions_button = Button(520, 580, 230, 80, "Ayuda", font,
                                 color=(220, 100, 60), hover_color=(255, 140, 80))

    show_instructions = False
    title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 70)
    subtitle_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 28)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        start_button.check_hover(mouse_pos)
        instructions_button.check_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            username_input.handle_event(event)
            ip_input.handle_event(event)
            port_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_clicked(mouse_pos):
                    return {
                        "username": username_input.text,
                        "ip": ip_input.text,
                        "port": port_input.text
                    }
                elif instructions_button.is_clicked(mouse_pos):
                    show_instructions = not show_instructions

        # Fondo con gradiente
        draw_gradient_background(screen, (15, 20, 35), (30, 40, 60))

        # Partículas decorativas (estrellas)
        time = pygame.time.get_ticks() / 1000
        for i in range(15):
            x = (i * 70 + time * 20) % screen.get_width()
            y = (i * 50) % screen.get_height()
            size = 2 + (i % 3)
            alpha = int(150 + 100 * abs((time + i) % 2 - 1))
            pygame.draw.circle(screen, (255, 255, 255, alpha), (int(x), int(y)), size)

        if show_instructions:
            # Panel de instrucciones
            panel_rect = pygame.Rect(180, 80, 640, 560)
            draw_panel(screen, panel_rect, (25, 30, 50), 240)

            # Título
            title = title_font.render("INSTRUCCIONES", True, (255, 200, 100))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 140))
            screen.blit(title, title_rect)

            # Instrucciones con iconos
            instructions = [
                ("", "MUEVES TU NAVE CON LAS FLECHAS"),
                ("", "DISPARAS CON SPACE"),
                ("", "QUE NO TE GOLPEEN LOS METEOROS"),
                ("", "TIENES 3 VIDAS"),
                ("", "DESTRUYE LOS METEOROS")

            ]

            icon_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 32)
            text_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 26)
            y_offset = 230

            for icon, text in instructions:
                icon_surf = icon_font.render(icon, True, (100, 200, 255))
                text_surf = text_font.render(text, True, (220, 220, 220))
                screen.blit(icon_surf, (230, y_offset))
                screen.blit(text_surf, (310, y_offset + 3))
                y_offset += 55
        else:
            # Panel de login
            panel_rect = pygame.Rect(250, 80, 500, 480)
            draw_panel(screen, panel_rect, (25, 30, 50), 240)

            # Título con efecto de brillo
            title = title_font.render("SPACE SHOOTER", True, (100, 200, 255))
            title_shadow = title_font.render("SPACE SHOOTER", True, (50, 100, 150))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 140))
            screen.blit(title_shadow, title_rect.move(3, 3))
            screen.blit(title, title_rect)

            # Subtítulo
            subtitle = subtitle_font.render("Multiplayer", True, (180, 180, 200))
            subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 195))
            screen.blit(subtitle, subtitle_rect)

            # Inputs
            username_input.draw(screen)
            ip_input.draw(screen)
            port_input.draw(screen)

        # Botones
        start_button.draw(screen)
        instructions_button.draw(screen)

        pygame.display.update()
        clock.tick(60)


def show_game_over_screen(screen, font, game_state, network):
    """Muestra la pantalla de Game Over mejorada"""
    clock = pygame.time.Clock()

    players_list = list(game_state.get("players", {}).values())
    players_list.sort(key=lambda p: p.get("score", 0), reverse=True)

    restart_button = Button(350, 670, 300, 80, "Play Again", font,
                            color=(80, 150, 255), hover_color=(120, 200, 255))

    title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
    header_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
    score_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 32)

    waiting = True
    animation_time = 0

    while waiting:
        dt = clock.tick(60) / 1000
        animation_time += dt

        mouse_pos = pygame.mouse.get_pos()
        restart_button.check_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.is_clicked(mouse_pos):
                    network.send_restart()
                    return True

        # Fondo con gradiente
        draw_gradient_background(screen, (20, 15, 30), (40, 30, 50))

        # Panel principal
        panel_rect = pygame.Rect(150, 60, 700, 590)
        draw_panel(screen, panel_rect, (30, 25, 45), 230)

        # Título animado
        pulse = 1 + 0.1 * abs((animation_time * 2) % 2 - 1)
        title_color = (255, int(80 + 50 * pulse), int(80 + 50 * pulse))
        title = title_font.render("GAME OVER", True, title_color)
        title_shadow = title_font.render("GAME OVER", True, (100, 30, 30))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 120))
        screen.blit(title_shadow, title_rect.move(4, 4))
        screen.blit(title, title_rect)

        # Header de tabla
        header = header_font.render("FINAL SCORE", True, (255, 220, 100))
        header_rect = header.get_rect(center=(screen.get_width() // 2, 200))
        screen.blit(header, header_rect)

        # Línea decorativa
        pygame.draw.line(screen, (100, 120, 150), (200, 235), (800, 235), 2)

        # Tabla de jugadores con diseño mejorado
        y_offset = 270
        for i, player in enumerate(players_list):
            if animation_time < (i + 1) * 0.3:
                continue

            position = f"#{i + 1}"
            username = player.get("username", f"Player{player.get('id')}")
            score = player.get("score", 0)
            lives = player.get("lives", 0)

            # Colores según posición
            if i == 0:
                bg_color = (255, 215, 0, 40)
                text_color = (255, 230, 100)
                medal = "Oro"
            elif i == 1:
                bg_color = (192, 192, 192, 40)
                text_color = (220, 220, 220)
                medal = "Plata"
            elif i == 2:
                bg_color = (205, 127, 50, 40)
                text_color = (230, 180, 130)
                medal = "Bronze"
            else:
                bg_color = (100, 100, 120, 30)
                text_color = (200, 200, 200)
                medal = " Loser "

            # Fondo de fila
            row_rect = pygame.Rect(200, y_offset - 5, 600, 50)
            row_surf = pygame.Surface(row_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(row_surf, bg_color, row_surf.get_rect(), border_radius=8)
            screen.blit(row_surf, row_rect)

            # Contenido
            pos_text = score_font.render(f"{medal} {position}", True, text_color)
            name_text = score_font.render(username, True, text_color)
            score_text = score_font.render(f"{score} pts", True, text_color)
            lives_text = score_font.render(f"❤ {lives}", True, text_color)

            screen.blit(pos_text, (220, y_offset))
            screen.blit(name_text, (360, y_offset))
            screen.blit(score_text, (570, y_offset))
            screen.blit(lives_text, (710, y_offset))

            y_offset += 70

        # Botón de reinicio
        restart_button.draw(screen)

        pygame.display.update()

    return False


def main():
    pygame.init()

    W_WIDTH, W_HEIGHT = 1000, 800
    screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
    pygame.display.set_caption("Space Shooter Multiplayer")
    clock = pygame.time.Clock()

    font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)

    # Pantalla de login
    login_data = show_login_screen(screen, font)
    if not login_data:
        pygame.quit()
        return

    # Conectar al servidor
    network = Network()
    if not network.connect(login_data["ip"], login_data["port"], login_data["username"]):
        print("No se pudo conectar al servidor")
        pygame.quit()
        return

    import time
    time.sleep(0.5)

    # Cargar recursos
    bg_surf = pygame.image.load(join('images', 'bg.jpg')).convert()
    laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
    meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
    life_surf = pygame.image.load(join('images', 'life.png')).convert_alpha()
    explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

    laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
    laser_sound.set_volume(0.5)
    explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
    explosion_sound.set_volume(0.4)
    damage_sound = pygame.mixer.Sound(join('audio', 'damage.wav'))
    damage_sound.set_volume(0.6)
    game_sound = pygame.mixer.Sound(join('audio', 'game_music.wav'))
    game_sound.set_volume(0.4)
    game_sound.play(loops=-1)

    star_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()

    player = Player(all_sprites, W_WIDTH, W_HEIGHT, laser_surf, all_sprites, laser_sprites, laser_sound,
                    network.player_id)

    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    for i in range(20):
        Star(star_sprites, star_surf, W_WIDTH, W_HEIGHT)

    meteor_event = pygame.event.custom_type()
    pygame.time.set_timer(meteor_event, 500)

    player_lives = 3
    player_score = 0
    running = True
    last_position_update = 0
    position_update_interval = 0.05

    # Pantalla de espera mejorada
    waiting_for_players = True
    wait_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 45)
    small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 32)

    while waiting_for_players and running:
        game_state = network.get_game_state()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                waiting_for_players = False

        # Fondo con gradiente
        draw_gradient_background(screen, (15, 20, 35), (30, 40, 60))

        # Panel de espera
        panel_rect = pygame.Rect(200, 300, 600, 200)
        draw_panel(screen, panel_rect, (30, 35, 55), 240)

        num_players = game_state.get("num_players", 0)
        status = game_state.get("status", "waiting")

        if status == "ready":
            waiting_text = wait_font.render("Waiting for server...", True, (255, 220, 100))
        else:
            waiting_text = wait_font.render(f"Players: {num_players}/4", True, (100, 200, 255))

        waiting_rect = waiting_text.get_rect(center=(W_WIDTH // 2, 370))
        screen.blit(waiting_text, waiting_rect)

        # Texto parpadeante
        if pygame.time.get_ticks() % 1000 < 500:
            status_text = small_font.render("Connecting...", True, (150, 150, 180))
            status_rect = status_text.get_rect(center=(W_WIDTH // 2, 430))
            screen.blit(status_text, status_rect)

        if game_state.get("status") == "running":
            waiting_for_players = False

        pygame.display.update()
        clock.tick(60)

    # Loop principal
    hud_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 28)
    score_font_big = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 50)

    while running:
        dt = clock.tick(60) / 1000
        events = pygame.event.get()

        game_state = network.get_game_state()

        if player_lives <= 0:
            restart = show_game_over_screen(screen, font, game_state, network)
            if restart:
                player_lives = 3
                player_score = 0
                player.rect.center = (W_WIDTH / 2, W_HEIGHT / 2)
                meteor_sprites.empty()
                laser_sprites.empty()

                waiting_restart = True
                while waiting_restart:
                    game_state = network.get_game_state()
                    if game_state.get("status") == "running":
                        waiting_restart = False

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            waiting_restart = False

                    draw_gradient_background(screen, (15, 20, 35), (30, 40, 60))
                    panel_rect = pygame.Rect(250, 350, 500, 100)
                    draw_panel(screen, panel_rect, (30, 35, 55), 240)
                    wait_text = font.render("Waiting for players...", True, (100, 200, 255))
                    wait_rect = wait_text.get_rect(center=(W_WIDTH // 2, 400))
                    screen.blit(wait_text, wait_rect)
                    pygame.display.update()
                    clock.tick(60)
            else:
                running = False
            continue

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == meteor_event:
                x = randint(0, W_WIDTH)
                y = randint(-200, -100)
                Meteor([all_sprites, meteor_sprites], meteor_surf, (x, y))

        star_sprites.update(dt, events)
        all_sprites.update(dt, events)

        current_time = pygame.time.get_ticks() / 1000
        if current_time - last_position_update > position_update_interval:
            network.send_position(player.rect.centerx, player.rect.centery)
            last_position_update = current_time

        collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True)
        if collision_sprites:
            player_lives -= 1
            network.send_hit()
            damage_sound.play()
            Explosion(explosion_frames, all_sprites, player.rect.center)

        for laser in laser_sprites:
            collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
            if collided_sprites:
                laser.kill()
                Explosion(explosion_frames, all_sprites, laser.rect.midtop)
                explosion_sound.play()
                player_score += 10
                network.send_score(player_score)

        # Renderizado
        screen.fill('#1a1a2e')

        # Panel de puntaje principal (centro inferior)
        score_panel_rect = pygame.Rect(W_WIDTH // 2 - 120, W_HEIGHT - 100, 240, 70)
        draw_panel(screen, score_panel_rect, (40, 80, 140), 200)

        score_text = score_font_big.render(str(player_score), True, (255, 255, 100))
        score_rect = score_text.get_rect(center=score_panel_rect.center)
        screen.blit(score_text, score_rect)

        # Panel de vidas (esquina superior izquierda)
        lives_panel_rect = pygame.Rect(10, 10, 160, 60)
        draw_panel(screen, lives_panel_rect, (140, 40, 80), 200)

        for i in range(player_lives):
            screen.blit(life_surf, (25 + i * 45, 18))

        # Panel de otros jugadores (esquina superior derecha)
        if game_state.get("players"):
            other_players = {k: v for k, v in game_state.get("players", {}).items() if k != network.player_id}
            if other_players:
                players_panel_rect = pygame.Rect(W_WIDTH - 330, 10, 320, 40 + len(other_players) * 35)
                draw_panel(screen, players_panel_rect, (60, 40, 80), 200)

                y_offset = 20
                for player_id, pdata in other_players.items():
                    username = pdata.get("username", f"P{player_id}")
                    score = pdata.get("score", 0)
                    lives = pdata.get("lives", 0)
                    text = hud_font.render(f"{username}: {score} pts (❤{lives})", True, (220, 220, 220))
                    screen.blit(text, (W_WIDTH - 315, y_offset))
                    y_offset += 35

        star_sprites.draw(screen)
        all_sprites.draw(screen)

        pygame.display.update()

    network.disconnect()
    pygame.quit()


if __name__ == "__main__":
    main()