"""
Servidor para el juego de naves espaciales multijugador.
Gestiona hasta 4 jugadores y sincroniza el estado del juego.

Este módulo implementa un servidor TCP que maneja múltiples conexiones
de clientes usando threading para permitir el juego multijugador.
"""

import socket
import threading
import json
import time
import pygame
from os.path import join

# Configuración del servidor
HOST = "0.0.0.0"  # Escucha en todas las interfaces de red disponibles
PORT = 5555  # Puerto donde el servidor va a escuchar conexiones
MAX_PLAYERS = 4  # Máximo de jugadores permitidos en una partida
MIN_PLAYERS = 2  # Mínimo de jugadores para iniciar el juego

# Estado global del juego - Este diccionario guarda toda la info del juego
game_state = {
    "status": "waiting",  # Estados posibles: waiting, ready, running, finished
    "players": {},  # Diccionario con info de cada jugador conectado
    "meteors": [],  # Lista de meteoritos activos (no se usa mucho aquí)
    "num_players": 0  # Contador de jugadores conectados
}

# Lock para evitar condiciones de carrera cuando varios threads acceden al estado
lock = threading.Lock()
clients = []  # Lista de sockets de clientes conectados
player_count = 0  # Contador global para asignar IDs únicos a jugadores

game_started = False  # Marca para saber si el juego ya comenzó


def broadcast_state():
    """
    Envía el estado del juego a todos los clientes conectados.

    Esta función serializa el estado del juego a JSON y lo envía
    a cada cliente. Si algún cliente se desconectó, lo elimina de la lista.
    """
    # Creamos el mensaje con el estado actual del juego
    state_message = {"type": "state", "state": game_state}
    # Convertimos a JSON y agregamos salto de línea para delimitar mensajes
    message = (json.dumps(state_message) + "\n").encode("utf-8")

    with lock:  # Bloqueamos para evitar problemas de concurrencia
        disconnected = []  # Lista para guardar clientes desconectados

        # Intentamos enviar el mensaje a cada cliente
        for client_socket in clients:
            try:
                client_socket.sendall(message)
            except:
                # Si falla, el cliente se desconectó
                disconnected.append(client_socket)

        # Removemos los clientes desconectados de la lista
        for client_socket in disconnected:
            if client_socket in clients:
                clients.remove(client_socket)


def handle_client(conn, addr):
    """
    Maneja la conexión de un cliente individual en un thread separado.

    Argumentos:
        conn: Socket de conexión con el cliente
        addr: Dirección IP y puerto del cliente

    Esta función procesa todos los mensajes que envía un cliente
    y actualiza el estado del juego según las acciones recibidas.
    """
    global player_count
    player_id = -1  # ID del jugador, se asigna después

    try:
        with lock:
            # Verificamos si ya hay demasiados jugadores
            if len(game_state["players"]) >= MAX_PLAYERS:
                conn.close()
                return

            # Asignamos un ID único al nuevo jugador
            player_count += 1
            player_id = player_count

            # Inicializamos los datos del jugador en el estado del juego
            game_state["players"][player_id] = {
                "id": player_id,
                "username": f"Player{player_id}",  # Nombre
                "x": 500,  # Posición inicial X
                "y": 500,  # Posición inicial Y
                "lives": 3,  # Vidas iniciales
                "score": 0,  # Puntaje inicial
                "alive": True  # Estado del jugador
            }
            game_state["num_players"] = len(game_state["players"])

        print(f"Jugador {player_id} conectado desde {addr}")

        # Enviamos mensaje de bienvenida con el ID asignado
        welcome = {"type": "welcome", "player_id": player_id}
        conn.sendall((json.dumps(welcome) + "\n").encode("utf-8"))
        broadcast_state()  # Notificamos a todos del nuevo jugador

        with lock:
            # Si ya hay suficientes jugadores, cambiamos el estado a "ready"
            if game_state["num_players"] >= MIN_PLAYERS:
                game_state["status"] = "ready"
                print(f"¡{game_state['num_players']} jugadores conectados! Esperando señal de inicio...")

        # Procesamos mensajes del cliente línea por línea
        conn_file = conn.makefile(mode="r")
        for line in conn_file:
            try:
                msg = json.loads(line.strip())  # Convertimos el JSON
                action = msg.get("action")  # Obtenemos la acción solicitada

                with lock:
                    # Verificamos que el jugador aún exista
                    if player_id not in game_state["players"]:
                        continue

                    pdata = game_state["players"][player_id]

                    # Procesamos diferentes tipos de acciones
                    if action == "join":
                        # El jugador envía su nombre de usuario
                        pdata["username"] = msg.get("username", f"Player{player_id}")

                    elif action == "update_position":
                        # Actualizamos la posición del jugador
                        pdata["x"] = msg.get("x")
                        pdata["y"] = msg.get("y")

                    elif action == "update_score":
                        # Actualizamos el puntaje del jugador
                        pdata["score"] = msg.get("score")

                    elif action == "hit":
                        # El jugador fue golpeado por un meteorito
                        pdata["lives"] -= 1
                        if pdata["lives"] <= 0:
                            pdata["alive"] = False
                            # Verificamos si todos los jugadores murieron
                            alive_players = [p for p in game_state["players"].values() if p["alive"]]
                            if len(alive_players) == 0:
                                game_state["status"] = "finished"

                    elif action == "restart":
                        # El jugador quiere reiniciar
                        pdata["lives"] = 3
                        pdata["score"] = 0
                        pdata["alive"] = True
                        # Si todos están vivos, reiniciamos el juego
                        all_alive = all(p["alive"] for p in game_state["players"].values())
                        if all_alive:
                            game_state["status"] = "running"

                # Enviamos el estado actualizado a todos
                broadcast_state()

            except json.JSONDecodeError:
                # Si el JSON está mal formado, lo ignoramos
                continue

    except Exception as e:
        print(f"Error con jugador {player_id}: {e}")
    finally:
        # Limpieza cuando el cliente se desconecta
        with lock:
            if player_id in game_state["players"]:
                del game_state["players"][player_id]
                game_state["num_players"] = len(game_state["players"])
        conn.close()
        print(f"Jugador {player_id} desconectado")
        broadcast_state()


def start_server_thread():
    """
    Inicia el servidor en un hilo separado.

    Crea un socket TCP, lo configura para escuchar conexiones
    y acepta clientes en un loop infinito. Cada cliente se maneja
    en su propio thread.
    """
    # Creamos el socket TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permitimos reusar la dirección inmediatamente después de cerrar
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Vinculamos el socket al host y puerto
    server.bind((HOST, PORT))
    # Empezamos a escuchar conexiones (cola de hasta MAX_PLAYERS)
    server.listen(MAX_PLAYERS)
    print(f"Servidor iniciado en {HOST}:{PORT}")
    print(f"Esperando hasta {MAX_PLAYERS} jugadores...")

    # Loop infinito para aceptar clientes
    while True:
        conn, addr = server.accept()  # Bloquea hasta que llegue un cliente
        with lock:
            clients.append(conn)  # Agregamos el cliente a la lista
        # Creamos un thread daemon para manejar este cliente
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


def draw_gradient_background(screen, color1, color2):
    """
    Dibuja un fondo con gradiente vertical.

    Argumentos:
        screen: Superficie de pygame donde dibujar
        color1: Color RGB superior del gradiente
        color2: Color RGB inferior del gradiente

    Dibuja líneas horizontales interpolando entre los dos colores
    para crear un efecto de gradiente suave.
    """
    height = screen.get_height()
    for y in range(height):
        # Calculamos cuánto se mezcla el color inicial con el final (de 0 a 1)
        ratio = y / height
        # Combinamos cada componente RGB
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        # Dibujamos una línea horizontal con el color interpolado
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


def draw_panel(screen, rect, color=(30, 35, 55), alpha=220):
    """
    Dibuja un panel decorativo con sombra y bordes redondeados.

    Argumentos:
        screen: Superficie donde dibujar
        rect: Rectángulo que define la posición y tamaño del panel
        color: Color RGB del panel
        alpha: Transparencia del panel (0-255)

    Crea un efecto visual moderno con sombra, transparencia y bordes brillantes.
    """
    # Dibujamos la sombra (un poco más grande que el panel)
    shadow_rect = rect.copy()
    shadow_rect.inflate_ip(8, 8)  # Agrandamos 8 píxeles en cada dirección
    shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(), border_radius=20)
    screen.blit(shadow_surf, shadow_rect)

    # Dibujamos el panel principal con transparencia
    panel_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (*color, alpha), panel_surf.get_rect(), border_radius=20)
    screen.blit(panel_surf, rect)

    # Dibujamos un borde brillante
    pygame.draw.rect(screen, (100, 120, 180, 150), rect, 2, border_radius=20)


def draw_button(screen, rect, text, font, hovered, active=True):
    """
    Dibuja un botón moderno con efectos visuales.

    Argumentos:
        screen: Superficie donde dibujar
        rect: Rectángulo del botón
        text: Texto a mostrar en el botón
        font: Fuente de pygame para el texto
        hovered: Boolean que indica si el mouse está sobre el botón
        active: Boolean que indica si el botón está activo

    Cambia de color según el estado (hover, activo/inactivo) y
    agrega efectos de sombra y bordes.
    """
    # Definimos colores según el estado del botón
    if not active:
        color = (80, 80, 100)  # Gris si está inactivo
        border_color = (120, 120, 140)
    else:
        # Verde más brillante si está en hover
        color = (80, 220, 150) if hovered else (60, 180, 120)
        border_color = (255, 255, 255) if hovered else (200, 200, 200)

    # Dibujamos sombra del botón
    shadow_rect = rect.copy()
    shadow_rect.y += 4  # Desplazamos la sombra hacia abajo
    pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)

    # Dibujamos el botón principal
    pygame.draw.rect(screen, color, rect, border_radius=15)

    # Dibujamos el borde
    pygame.draw.rect(screen, border_color, rect, 4, border_radius=15)

    # Renderizamos y centramos el texto
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def draw_status_indicator(screen, x, y, status):
    """
    Dibuja un indicador de estado con color pulsante.

    Argumentos:
        screen: Superficie donde dibujar
        x, y: Coordenadas del centro del indicador
        status: Estado actual ("waiting", "ready", "running", "finished")

    Muestra un círculo de color que pulsa para indicar el estado del servidor.
    """
    # Mapeamos cada estado a un color específico
    colors = {
        "waiting": (255, 200, 100),  # Naranja - esperando
        "ready": (100, 200, 255),  # Azul - listo
        "running": (100, 255, 150),  # Verde - corriendo
        "finished": (255, 100, 100)  # Rojo - terminado
    }

    color = colors.get(status, (150, 150, 150))  # Gris por defecto

    # Calculamos el efecto de pulso usando el tiempo
    pulse = 1 + 0.2 * abs((pygame.time.get_ticks() / 500) % 2 - 1)
    radius = int(8 * pulse)

    # Dibujamos el círculo con el color correspondiente
    pygame.draw.circle(screen, color, (x, y), radius)
    # Dibujamos el borde blanco
    pygame.draw.circle(screen, (255, 255, 255), (x, y), radius, 2)


def run_server_gui():
    """
    Ejecuta la interfaz gráfica del servidor

    Esta función crea una ventana de pygame que muestra:
    - Estado del servidor
    - Jugadores conectados
    - Botón para iniciar el juego
    - Información en tiempo real

    Es el loop principal de la GUI del servidor.
    """
    global game_started

    # Inicializamos pygame y creamos la ventana
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Space Shooter Server")
    clock = pygame.time.Clock()

    # Cargamos diferentes fuentes para la interfaz
    title_font = pygame.font.Font(None, 70)
    font = pygame.font.Font(None, 45)
    small_font = pygame.font.Font(None, 32)
    info_font = pygame.font.Font(None, 28)

    # Definimos el rectángulo del botón de inicio
    start_button_rect = pygame.Rect(250, 480, 300, 80)

    # Creamos partículas decorativas para el fondo
    particles = []
    for i in range(20):
        particles.append({
            "x": (i * 40) % 800,
            "y": (i * 30) % 600,
            "speed": 20 + (i % 5) * 10  # Velocidades variadas
        })

    running = True
    animation_time = 0  # Tiempo para animaciones

    # Loop principal de la GUI
    while running:
        dt = clock.tick(60) / 1000  # Delta time en segundos
        animation_time += dt

        mouse_pos = pygame.mouse.get_pos()
        button_hovered = start_button_rect.collidepoint(mouse_pos)

        # Procesamos eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Si dan click en el botón y hay suficientes jugadores
                if button_hovered and game_state["num_players"] >= MIN_PLAYERS and not game_started:
                    with lock:
                        game_state["status"] = "running"
                        game_started = True
                    broadcast_state()
                    print("¡Juego iniciado!")

        # Dibujamos el fondo con gradiente
        draw_gradient_background(screen, (20, 25, 40), (40, 45, 70))

        # Animamos las partículas de fondo
        for particle in particles:
            particle["y"] = (particle["y"] + particle["speed"] * dt) % 600
            size = 2 + (particle["speed"] // 20)
            alpha = 150
            pygame.draw.circle(screen, (255, 255, 255, alpha),
                               (int(particle["x"]), int(particle["y"])), size)

        # Dibujamos el panel principal
        main_panel_rect = pygame.Rect(50, 50, 700, 380)
        draw_panel(screen, main_panel_rect, (30, 35, 55), 240)

        # Dibujamos el título con efecto de sombra
        title = title_font.render("SERVER CONTROL", True, (100, 200, 255))
        title_shadow = title_font.render("SERVER CONTROL", True, (50, 100, 150))
        title_rect = title.get_rect(center=(400, 100))
        screen.blit(title_shadow, title_rect.move(3, 3))  # Sombra desplazada
        screen.blit(title, title_rect)

        # Panel de información del servidor
        server_panel_rect = pygame.Rect(80, 150, 640, 60)
        draw_panel(screen, server_panel_rect, (40, 50, 80), 200)

        server_info = info_font.render(f"Host: {HOST}:{PORT}", True, (200, 220, 255))
        screen.blit(server_info, (100, 165))

        # Indicador de estado del servidor
        status = game_state.get("status", "waiting")
        draw_status_indicator(screen, 620, 180, status)

        # Texto del estado
        status_texts = {
            "waiting": "Waiting",
            "ready": "Ready",
            "running": "Running",
            "finished": "Finished"
        }
        status_text = info_font.render(status_texts.get(status, "Unknown"), True, (220, 220, 220))
        screen.blit(status_text, (640, 165))

        # Contador de jugadores
        num_players = game_state.get("num_players", 0)
        players_panel_rect = pygame.Rect(80, 230, 640, 60)
        draw_panel(screen, players_panel_rect, (50, 40, 80), 200)

        players_text = font.render(f"Players: {num_players}/{MAX_PLAYERS}", True, (255, 255, 255))
        screen.blit(players_text, (100, 240))

        # Barra de progreso de jugadores
        progress_width = 200
        progress_rect = pygame.Rect(450, 245, progress_width, 30)
        pygame.draw.rect(screen, (40, 40, 60), progress_rect, border_radius=15)

        if num_players > 0:
            # Calculamos el ancho de la barra según jugadores conectados
            filled_width = int((num_players / MAX_PLAYERS) * progress_width)
            filled_rect = pygame.Rect(450, 245, filled_width, 30)

            # Color verde si hay suficientes jugadores, naranja si no
            if num_players >= MIN_PLAYERS:
                color = (100, 255, 150)
            else:
                color = (255, 200, 100)

            pygame.draw.rect(screen, color, filled_rect, border_radius=15)

        pygame.draw.rect(screen, (100, 120, 150), progress_rect, 2, border_radius=15)

        # Lista de jugadores conectados
        if game_state.get("players"):
            players_list_panel = pygame.Rect(80, 310, 640, 110)
            draw_panel(screen, players_list_panel, (40, 45, 70), 200)

            list_title = small_font.render("Jugadores conectados:", True, (180, 200, 255))
            screen.blit(list_title, (100, 320))

            y_offset = 355
            x_offset = 120
            col = 0

            # Mostramos cada jugador con su info
            for player_id, pdata in game_state.get("players", {}).items():
                username = pdata.get("username", f"Player{player_id}")
                lives = pdata.get("lives", 3)
                score = pdata.get("score", 0)
                alive = pdata.get("alive", True)

                # Color según si está vivo o muerto
                if alive:
                    name_color = (150, 255, 150)  # Verde
                    icon = "●"  # Círculo lleno
                else:
                    name_color = (255, 100, 100)  # Rojo
                    icon = "○"  # Círculo vacío

                player_text = info_font.render(f"{icon} {username}", True, name_color)
                screen.blit(player_text, (x_offset, y_offset))

                stats_text = info_font.render(f"({score} pts, {lives})", True, (200, 200, 200))
                screen.blit(stats_text, (x_offset + 150, y_offset))

                # Organizamos en dos columnas
                col += 1
                if col % 2 == 0:
                    y_offset += 35
                    x_offset = 120
                else:
                    x_offset = 420

        # Botón de inicio o mensaje de estado según la situación
        if game_state["num_players"] >= MIN_PLAYERS and not game_started:
            draw_button(screen, start_button_rect, "Iniciando", font, button_hovered, True)
        elif game_state["status"] == "Corriendo":
            status_panel = pygame.Rect(250, 480, 300, 80)
            draw_panel(screen, status_panel, (50, 150, 100), 220)
            status_msg = small_font.render("Jugando...", True, (150, 255, 150))
            status_rect = status_msg.get_rect(center=status_panel.center)
            screen.blit(status_msg, status_rect)
        elif game_state["status"] == "Terminado":
            status_panel = pygame.Rect(250, 480, 300, 80)
            draw_panel(screen, status_panel, (150, 50, 50), 220)
            status_msg = small_font.render("Juego terminado", True, (255, 150, 150))
            status_rect = status_msg.get_rect(center=status_panel.center)
            screen.blit(status_msg, status_rect)
        else:
            status_panel = pygame.Rect(200, 480, 400, 80)
            draw_panel(screen, status_panel, (80, 80, 100), 220)

            # Mensaje según cuántos jugadores faltan
            if num_players == 0:
                msg = "Esperando jugadores..."
            else:
                msg = f"Necesita {MIN_PLAYERS - num_players} mas jugador(es)"

            status_msg = small_font.render(msg, True, (200, 200, 200))
            status_rect = status_msg.get_rect(center=status_panel.center)

            # Texto parpadeante
            if pygame.time.get_ticks() % 1000 < 500:
                screen.blit(status_msg, status_rect)

        pygame.display.update()

    pygame.quit()


# Punto de entrada del programa
if __name__ == "__main__":
    # Iniciamos el servidor en un thread separado para no bloquear la GUI
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()

    # Ejecutamos la interfaz gráfica en el thread principal
    run_server_gui()
