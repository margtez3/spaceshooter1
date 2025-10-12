"""
Archivo principal del juego Space Shooter Multiplayer.

Este es el punto de entrada del juego. Maneja:
- Pantalla de login
- Conexión al servidor
- Loop principal del juego
- Pantalla de game over
- Interfaz de usuario (HUD)
"""

import pygame
from os.path import join
from random import randint
from player import Player
from star import Star
from meteor import Meteor
from network import Network


class Explosion(pygame.sprite.Sprite):
    """
    Clase que representa una animación de explosión.

    Muestra una secuencia de frames para crear el efecto visual
    de una explosión cuando un meteorito es destruido.

    Atributos:
        frames: Lista de imágenes de la animación
        index: Índice del frame actual
        image: Imagen actual que se está mostrando
        rect: Rectángulo para posicionar la explosión
    """

    def __init__(self, frames, groups, pos):
        """
        Inicializa una explosión en la posición dada.

        Argumentos:
            frames: Lista de superficies con los frames de la animación
            groups: Grupos de sprites a los que pertenece
            pos: Tupla (x, y) con la posición de la explosión
        """
        super().__init__(groups)
        self.frames = frames
        self.index = 0  # Empezamos en el primer frame
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt, events=None):
        """
        Actualiza la animación de la explosión.

        Argumentos:
            dt: Delta time en segundos
            events: Lista de eventos (no se usa)

        Avanza por los frames de la animación y se destruye al terminar.
        """
        # Avanzamos el índice (20 frames por segundo)
        self.index += 20 * dt

        # Si aún hay frames por mostrar
        if self.index < len(self.frames):
            self.image = self.frames[int(self.index)]
        else:
            # La animación terminó, eliminamos el sprite
            self.kill()


class Button:
    """
    Clase que representa un botón en la interfaz.

    Maneja la apariencia visual del botón, efectos de hover
    y detección de clicks.

    Atributos:
        rect: Rectángulo que define posición y tamaño
        text: Texto a mostrar en el botón
        font: Fuente de pygame para el texto
        color: Color normal del botón
        hover_color: Color cuando el mouse está encima
        text_color: Color del texto
        is_hovered: Boolean que indica si el mouse está sobre el botón
    """

    def __init__(self, x, y, width, height, text, font,
                 color=(180, 140, 255), hover_color=(255, 100, 150)):
        """
        Inicializa un botón con su posición y estilo.

        Argumentos:
            x, y: Coordenadas de la esquina superior izquierda
            width, height: Dimensiones del botón
            text: Texto a mostrar
            font: Fuente de pygame
            color: Color RGB normal
            hover_color: Color RGB en hover
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = (255, 255, 255)  # Blanco
        self.is_hovered = False

    def draw(self, screen):
        """
        Dibuja el botón en la pantalla con efectos visuales.

        Argumentos:
            screen: Superficie de pygame donde dibujar

        Dibuja sombra, fondo, borde y texto del botón.
        """
        # Seleccionamos el color según el estado de hover
        color = self.hover_color if self.is_hovered else self.color

        # Dibujamos la sombra del botón
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)

        # Dibujamos el botón principal
        pygame.draw.rect(screen, color, self.rect, border_radius=15)

        # Dibujamos el borde brillante
        border_color = (255, 255, 255) if self.is_hovered else (200, 200, 200)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=15)

        # Renderizamos y centramos el texto
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        """
        Verifica si el mouse está sobre el botón.

        Argumentos:
            pos: Tupla (x, y) con la posición del mouse
        """
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        """
        Verifica si el botón fue presionado.

        Argumentos:
            pos: Tupla (x, y) con la posición del click

        Returns:
            bool: True si el click fue dentro del botón
        """
        return self.rect.collidepoint(pos)


class InputBox:
    """
    Clase para campos de entrada de texto.

    Permite al usuario escribir texto con el teclado,
    con efectos visuales y cursor parpadeante.

    Atributos:
        rect: Rectángulo del campo de entrada
        color_inactive: Color cuando no está seleccionado
        color_active: Color cuando está seleccionado
        color: Color actual
        font: Fuente para el texto
        label: Etiqueta que se muestra arriba del campo
        text: Texto actual ingresado
        active: Boolean que indica si está seleccionado
    """

    def __init__(self, x, y, width, height, font, label, default_text=''):
        """
        Inicializa un campo de entrada de texto.

        Argumentos:
            x, y: Posición del campo
            width, height: Dimensiones del campo
            font: Fuente de pygame
            label: Texto de la etiqueta
            default_text: Texto inicial (opcional)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = (60, 70, 100)  # Gris azulado
        self.color_active = (80, 140, 220)  # Azul brillante
        self.color = self.color_inactive
        self.font = font
        self.label = label
        self.text = default_text
        self.active = False  # No está seleccionado al inicio

    def handle_event(self, event):
        """
        Maneja eventos de teclado y mouse para el campo de entrada.

        Args:
            event: Evento de pygame a procesar

        Detecta clicks para activar/desactivar el campo y teclas
        para agregar/borrar texto.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Si presionan dentro del campo, lo activamos
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                # Si presionan fuera, lo desactivamos
                self.active = False
            # Actualizamos el color según el estado
            self.color = self.color_active if self.active else self.color_inactive

        # Solo procesamos teclas si el campo está activo
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                # Borramos el último carácter
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                # Enter desactiva el campo
                self.active = False
                self.color = self.color_inactive
            else:
                # Agregamos el carácter presionado
                self.text += event.unicode

    def draw(self, screen):
        """
        Dibuja el campo de entrada.

        Argumentos:
            screen: Superficie donde dibujar

        Dibuja la etiqueta, el fondo, el borde, el texto y el cursor.
        """
        # Dibujamos la etiqueta arriba del campo
        label_surf = self.font.render(self.label, True, (200, 220, 255))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 35))

        # Dibujamos el fondo del input con efecto de profundidad
        background_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(screen, (20, 25, 40), background_rect, border_radius=8)

        # Dibujamos el borde del input
        border_color = self.color if self.active else (100, 110, 140)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=8)

        # Renderizamos el texto ingresado
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (self.rect.x + 15, self.rect.y + 12))

        # Dibujamos cursor parpadeante si está activo
        if self.active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = self.rect.x + 15 + text_surf.get_width() + 2
            pygame.draw.line(screen, (255, 255, 255),
                             (cursor_x, self.rect.y + 10),
                             (cursor_x, self.rect.y + self.rect.height - 10), 2)


def draw_gradient_background(screen, color1, color2):
    """
    Dibuja un fondo con gradiente vertical.

    Argumentos:
        screen: Superficie de pygame donde dibujar
        color1: Color RGB superior del gradiente
        color2: Color RGB inferior del gradiente

    Crea un efecto de gradiente suave interpolando entre dos colores.
    """
    height = screen.get_height()
    for y in range(height):
       #Calculamos cuánto se mezcla el color inicial con el final (de 0 a 1)
        ratio = y / height
        # Combinación de cada componente RGB
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        # Dibujamos una línea horizontal con el color combinado
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


def draw_panel(screen, rect, color=(30, 35, 55), alpha=220):
    """
    Dibuja un panel decorativo con sombra y transparencia.

    Argumentos:
        screen: Superficie donde dibujar
        rect: Rectángulo que define posición y tamaño
        color: Color RGB del panel
        alpha: Nivel de transparencia (0-255)

    Crea paneles con efecto moderno para la interfaz.
    """
    # Dibujamos la sombra
    shadow_rect = rect.copy()
    shadow_rect.inflate_ip(8, 8)
    shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(), border_radius=20)
    screen.blit(shadow_surf, shadow_rect)

    # Dibujamos el panel principal con transparencia
    panel_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (*color, alpha), panel_surf.get_rect(), border_radius=20)
    screen.blit(panel_surf, rect)

    # Dibujamos un borde brillante
    pygame.draw.rect(screen, (100, 120, 180, 150), rect, 2, border_radius=20)


def show_login_screen(screen, font):
    """
    Muestra la pantalla de login.

    Argumentos:
        screen: Superficie de pygame
        font: Fuente para el texto

    Returns:
        dict o None: Diccionario con username, ip y port si el usuario
                     presiona Start, None si cierra la ventana

    Permite al usuario ingresar su nombre, IP del servidor y puerto
    antes de conectarse al juego.
    """
    clock = pygame.time.Clock()

    # Creamos los campos de entrada con valores por defecto
    username_input = InputBox(325, 260, 350, 55, font, "Username:", "Player1")
    ip_input = InputBox(325, 360, 350, 55, font, "Server IP:", "127.0.0.1")
    port_input = InputBox(325, 460, 350, 55, font, "Port:", "5555")

    # Creamos los botones
    start_button = Button(280, 580, 220, 75, "Start", font,
                          color=(60, 180, 120), hover_color=(80, 220, 150))
    instructions_button = Button(520, 580, 220, 75, "Ayuda", font,
                                 color=(220, 100, 60), hover_color=(255, 140, 80))

    show_instructions = False  # Bandera para mostrar/ocultar instrucciones

    # Cargamos fuentes personalizadas
    title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 70)
    subtitle_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 28)

    # Loop principal de la pantalla de login
    while True:
        mouse_pos = pygame.mouse.get_pos()
        start_button.check_hover(mouse_pos)
        instructions_button.check_hover(mouse_pos)

        # Procesamos eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None  # El usuario cerró la ventana

            # Pasamos eventos a los campos de entrada
            username_input.handle_event(event)
            ip_input.handle_event(event)
            port_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_clicked(mouse_pos):
                    # Retornamos los datos ingresados
                    return {
                        "username": username_input.text,
                        "ip": ip_input.text,
                        "port": port_input.text
                    }
                elif instructions_button.is_clicked(mouse_pos):
                    # Alternamos la visualización de instrucciones
                    show_instructions = not show_instructions

        # Dibujamos el fondo con gradiente
        draw_gradient_background(screen, (15, 20, 35), (30, 40, 60))

        # Dibujamos estrellas
        time = pygame.time.get_ticks() / 1000
        for i in range(15):
            x = (i * 70 + time * 20) % screen.get_width()
            y = (i * 50) % screen.get_height()
            size = 2 + (i % 3)
            alpha = int(150 + 100 * abs((time + i) % 2 - 1))
            pygame.draw.circle(screen, (255, 255, 255, alpha), (int(x), int(y)), size)

        if show_instructions:
            # Mostramos el panel de instrucciones
            panel_rect = pygame.Rect(180, 80, 640, 560)
            draw_panel(screen, panel_rect, (25, 30, 50), 240)

            # Título
            title = title_font.render("¿Como jugar?", True, (255, 200, 100))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 140))
            screen.blit(title, title_rect)

            # Lista de instrucciones
            instructions = [
                ("", "Mueve tu nave con las flechas"),
                ("", "Dispara lasers con el espacio"),
                ("", "Esquiva meteoritos"),
                ("", "Tienes 3 vidas"),
                ("", "Destruye meteoritos")
            ]

            icon_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 32)
            text_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 26)
            y_offset = 230

            # Dibujamos cada instrucción
            for icon, text in instructions:
                icon_surf = icon_font.render(icon, True, (100, 200, 255))
                text_surf = text_font.render(text, True, (220, 220, 220))
                screen.blit(icon_surf, (230, y_offset))
                screen.blit(text_surf, (310, y_offset + 3))
                y_offset += 55
        else:
            # Mostramos el panel de login
            panel_rect = pygame.Rect(250, 80, 500, 480)
            draw_panel(screen, panel_rect, (25, 30, 50), 240)

            # Título con efecto de sombra
            title = title_font.render("SPACE SHOOTER", True, (100, 200, 255))
            title_shadow = title_font.render("SPACE SHOOTER", True, (50, 100, 150))
            title_rect = title.get_rect(center=(screen.get_width() // 2, 140))
            screen.blit(title_shadow, title_rect.move(3, 3))
            screen.blit(title, title_rect)

            # Subtítulo
            subtitle = subtitle_font.render("Multiplayer Edition", True, (180, 180, 200))
            subtitle_rect = subtitle.get_rect(center=(screen.get_width() // 2, 195))
            screen.blit(subtitle, subtitle_rect)

            # Dibujamos los campos de entrada
            username_input.draw(screen)
            ip_input.draw(screen)
            port_input.draw(screen)

        # Dibujamos los botones
        start_button.draw(screen)
        instructions_button.draw(screen)

        pygame.display.update()
        clock.tick(60)  # 60 FPS


def show_game_over_screen(screen, font, game_state, network):
    """
    Muestra la pantalla de Game Over con la tabla de puntajes.

    Argumentos:
        screen: Superficie de pygame
        font: Fuente para el texto
        game_state: Estado actual del juego con info de jugadores
        network: Objeto Network para enviar señal de reinicio

    Returns:
        bool: True si el usuario quiere jugar de nuevo, False si cierra

    Muestra los puntajes finales de todos los jugadores ordenados
    y permite reiniciar el juego.
    """
    clock = pygame.time.Clock()

    # Obtenemos la lista de jugadores y la ordenamos por puntaje
    players_list = list(game_state.get("players", {}).values())
    players_list.sort(key=lambda p: p.get("score", 0), reverse=True)

    # Creamos el botón de reinicio
    restart_button = Button(350, 670, 300, 80, "Play Again", font,
                            color=(80, 150, 255), hover_color=(120, 200, 255))

    # Cargamos imágenes
    title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
    header_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
    score_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 32)

    waiting = True
    animation_time = 0  # Para animaciones

    # Loop de la pantalla de game over
    while waiting:
        dt = clock.tick(60) / 1000
        animation_time += dt

        mouse_pos = pygame.mouse.get_pos()
        restart_button.check_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # El usuario cerró la ventana
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.is_clicked(mouse_pos):
                    # Enviamos señal de reinicio al servidor
                    network.send_restart()
                    return True  # Queremos jugar de nuevo

        # Dibujamos el fondo
        draw_gradient_background(screen, (20, 15, 30), (40, 30, 50))

        # Panel principal
        panel_rect = pygame.Rect(150, 60, 700, 590)
        draw_panel(screen, panel_rect, (30, 25, 45), 230)

        # Título animado con efecto
        pulse = 1 + 0.1 * abs((animation_time * 2) % 2 - 1)
        title_color = (255, int(80 + 50 * pulse), int(80 + 50 * pulse))
        title = title_font.render("GAME OVER", True, title_color)
        title_shadow = title_font.render("GAME OVER", True, (100, 30, 30))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 120))
        screen.blit(title_shadow, title_rect.move(4, 4))
        screen.blit(title, title_rect)

        # Header de la tabla
        header = header_font.render("FINAL SCORES", True, (255, 220, 100))
        header_rect = header.get_rect(center=(screen.get_width() // 2, 200))
        screen.blit(header, header_rect)

        # Línea decorativa
        pygame.draw.line(screen, (100, 120, 150), (200, 235), (800, 235), 2)

        # Tabla de jugadores con animación de entrada
        y_offset = 270
        for i, player in enumerate(players_list):
            # Animación: los jugadores aparecen uno por uno
            if animation_time < (i + 1) * 0.3:
                continue

            position = f"#{i + 1}"
            username = player.get("username", f"Player{player.get('id')}")
            score = player.get("score", 0)
            lives = player.get("lives", 0)

            # Colores según la posición (oro, plata, bronce)
            if i == 0:
                bg_color = (255, 215, 0, 40)  # Oro
                text_color = (255, 230, 100)
            elif i == 1:
                bg_color = (192, 192, 192, 40)  # Plata
                text_color = (220, 220, 220)
            elif i == 2:
                bg_color = (205, 127, 50, 40)  # Bronce
                text_color = (230, 180, 130)
            else:
                bg_color = (100, 100, 120, 30)  # Gris
                text_color = (200, 200, 200)

            # Dibujamos el fondo de la fila
            row_rect = pygame.Rect(200, y_offset - 5, 600, 50)
            row_surf = pygame.Surface(row_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(row_surf, bg_color, row_surf.get_rect(), border_radius=8)
            screen.blit(row_surf, row_rect)

            # Dibujamos el contenido de la fila
            pos_text = score_font.render(f" {position}", True, text_color)
            name_text = score_font.render(username, True, text_color)
            score_text = score_font.render(f"{score} pts", True, text_color)

            screen.blit(pos_text, (220, y_offset))
            screen.blit(name_text, (360, y_offset))
            screen.blit(score_text, (570, y_offset))

            y_offset += 70

        # Dibujamos el botón de reinicio
        restart_button.draw(screen)

        pygame.display.update()

    return False


def main():
    """
    Función principal del juego.

    Inicializa pygame, muestra la pantalla de login, conecta al servidor,
    carga recursos y ejecuta el loop principal del juego.
    """
    # Inicializamos pygame
    pygame.init()

    # Configuramos la ventana
    W_WIDTH, W_HEIGHT = 1000, 800
    screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
    pygame.display.set_caption("Space Shooter Multiplayer")
    clock = pygame.time.Clock()

    # Cargamos la fuente
    font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)

    # Mostramos la pantalla de login
    login_data = show_login_screen(screen, font)
    if not login_data:
        # El usuario cerró la ventana
        pygame.quit()
        return

    # Intentamos conectar al servidor
    network = Network()
    if not network.connect(login_data["ip"], login_data["port"], login_data["username"]):
        print("No se pudo conectar al servidor")
        pygame.quit()
        return

    # Esperamos un poco para que se establezca la conexión
    import time
    time.sleep(0.5)

    # Cargamos todos los recursos del juego
    laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
    meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
    life_surf = pygame.image.load(join('images', 'life.png')).convert_alpha()

    # Cargamos los frames de la explosión
    explosion_frames = [
        pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha()
        for i in range(21)
    ]

    # Cargamos y configuramos los sonidos
    laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
    laser_sound.set_volume(0.5)
    explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
    explosion_sound.set_volume(0.4)
    damage_sound = pygame.mixer.Sound(join('audio', 'demage.wav'))
    damage_sound.set_volume(0.6)
    game_sound = pygame.mixer.Sound(join('audio', 'game_music.wav'))
    game_sound.set_volume(0.4)
    game_sound.play(loops=-1)  # Música en loop infinito

    # Creamos los grupos de sprites
    star_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()

    # Creamos las estrellas de fondo
    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    for i in range(20):
        Star(star_sprites, star_surf, W_WIDTH, W_HEIGHT)

    # Creamos el jugador
    player = Player(all_sprites, W_WIDTH, W_HEIGHT, laser_surf, all_sprites,
                    laser_sprites, laser_sound, network.player_id)

    # Configuramos el evento de spawn de meteoritos
    meteor_event = pygame.event.custom_type()
    pygame.time.set_timer(meteor_event, 500)  # Cada 500ms

    # Variables del juego
    player_lives = 3
    player_score = 0
    running = True
    last_position_update = 0
    position_update_interval = 0.05  # Actualizamos posición cada 50ms

    # Pantalla de espera para que se conecten más jugadores
    waiting_for_players = True
    wait_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 45)
    small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 32)

    # Loop de espera
    while waiting_for_players and running:
        game_state = network.get_game_state()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                waiting_for_players = False

        # Dibujamos la pantalla de espera
        draw_gradient_background(screen, (15, 20, 35), (30, 40, 60))

        panel_rect = pygame.Rect(200, 300, 600, 200)
        draw_panel(screen, panel_rect, (30, 35, 55), 240)

        num_players = game_state.get("num_players", 0)
        status = game_state.get("status", "waiting")

        # Mensaje según el estado
        if status == "ready":
            waiting_text = wait_font.render("Esperando al servidor...", True, (255, 220, 100))
        else:
            waiting_text = wait_font.render(f"Players: {num_players}/4", True, (100, 200, 255))

        waiting_rect = waiting_text.get_rect(center=(W_WIDTH // 2, 370))
        screen.blit(waiting_text, waiting_rect)

        # Texto parpadeante
        if pygame.time.get_ticks() % 1000 < 500:
            status_text = small_font.render("Conectando...", True, (150, 150, 180))
            status_rect = status_text.get_rect(center=(W_WIDTH // 2, 430))
            screen.blit(status_text, status_rect)

        # Verificamos si el juego ya empezó
        if game_state.get("status") == "running":
            waiting_for_players = False

        pygame.display.update()
        clock.tick(60)

    # Fuentes para el HUD
    hud_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 28)
    score_font_big = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 50)

    # Loop principal del juego
    while running:
        dt = clock.tick(60) / 1000  # Delta time en segundos
        events = pygame.event.get()

        # Obtenemos el estado actualizado del juego
        game_state = network.get_game_state()

        # Verificamos si el jugador murió
        if player_lives <= 0:
            # Mostramos la pantalla de game over
            restart = show_game_over_screen(screen, font, game_state, network)

            if restart:
                # Reiniciamos las variables del jugador
                player_lives = 3
                player_score = 0
                player.rect.center = (W_WIDTH / 2, W_HEIGHT / 2)
                meteor_sprites.empty()
                laser_sprites.empty()

                # Esperamos a que todos los jugadores estén listos
                waiting_restart = True
                while waiting_restart:
                    game_state = network.get_game_state()
                    if game_state.get("status") == "running":
                        waiting_restart = False

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            waiting_restart = False

                    # Pantalla de espera
                    draw_gradient_background(screen, (15, 20, 35), (30, 40, 60))
                    panel_rect = pygame.Rect(250, 350, 500, 100)
                    draw_panel(screen, panel_rect, (30, 35, 55), 240)
                    wait_text = font.render("Esperando jugadores...", True, (100, 200, 255))
                    wait_rect = wait_text.get_rect(center=(W_WIDTH // 2, 400))
                    screen.blit(wait_text, wait_rect)
                    pygame.display.update()
                    clock.tick(60)
            else:
                running = False
            continue

        # Procesamos eventos
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == meteor_event:
                # Creamos un nuevo meteorito en posición aleatoria
                x = randint(0, W_WIDTH)
                y = randint(-200, -100)
                Meteor([all_sprites, meteor_sprites], meteor_surf, (x, y))

        # Actualizamos sprites
        star_sprites.update(dt, events)
        all_sprites.update(dt, events)

        # Enviamos la posición del jugador al servidor periódicamente
        current_time = pygame.time.get_ticks() / 1000
        if current_time - last_position_update > position_update_interval:
            network.send_position(player.rect.centerx, player.rect.centery)
            last_position_update = current_time

        # Detectamos colisiones entre jugador y meteoritos
        collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True)
        if collision_sprites:
            player_lives -= 1
            network.send_hit()  # Notificamos al servidor
            damage_sound.play()
            Explosion(explosion_frames, all_sprites, player.rect.center)

        # Detectamos colisiones entre láseres y meteoritos
        for laser in laser_sprites:
            collided_sprites = pygame.sprite.spritecollide(
                laser, meteor_sprites, True, pygame.sprite.collide_mask
            )
            if collided_sprites:
                laser.kill()  # Destruimos el láser
                Explosion(explosion_frames, all_sprites, laser.rect.midtop)
                explosion_sound.play()
                player_score += 10  # Sumamos puntos
                network.send_score(player_score)  # Actualizamos en el servidor

        # Renderizado
        screen.fill('#1a1a2e')  # Fondo oscuro

        # Panel de puntaje principal
        score_panel_rect = pygame.Rect(W_WIDTH // 2 - 120, W_HEIGHT - 100, 240, 70)
        draw_panel(screen, score_panel_rect, (40, 80, 140), 200)

        score_text = score_font_big.render(str(player_score), True, (255, 255, 100))
        score_rect = score_text.get_rect(center=score_panel_rect.center)
        screen.blit(score_text, score_rect)

        # Panel de vidas
        lives_panel_rect = pygame.Rect(10, 10, 160, 60)
        draw_panel(screen, lives_panel_rect, (140, 40, 80), 200)

        # Dibujamos los íconos de vidas
        for i in range(player_lives):
            screen.blit(life_surf, (25 + i * 45, 18))

        # Panel de otros jugadores
        if game_state.get("players"):
            # Filtramos para no mostrar nuestro propio jugador
            other_players = {
                k: v for k, v in game_state.get("players", {}).items()
                if k != network.player_id
            }

            if other_players:
                # Calculamos el tamaño del panel según la cantidad de jugadores
                players_panel_rect = pygame.Rect(
                    W_WIDTH - 330, 10, 320, 40 + len(other_players) * 35
                )
                draw_panel(screen, players_panel_rect, (60, 40, 80), 200)

                y_offset = 20
                # Mostramos info de cada jugador
                for player_id, pdata in other_players.items():
                    username = pdata.get("username", f"P{player_id}")
                    score = pdata.get("score", 0)
                    lives = pdata.get("lives", 0)
                    text = hud_font.render(
                        f"{username}: {score} pts ({lives})", True, (220, 220, 220)
                    )
                    screen.blit(text, (W_WIDTH - 315, y_offset))
                    y_offset += 35

        # Dibujamos todos los sprites
        star_sprites.draw(screen)
        all_sprites.draw(screen)

        pygame.display.update()

    # Limpieza al salir
    network.disconnect()
    pygame.quit()


# Punto de entrada del programa
if __name__ == "__main__":
    main()
