"""
Servidor para el juego de naves espaciales multijugador.
Gestiona hasta 4 jugadores y sincroniza el estado del juego.
"""

import socket
import threading
import json
import time
import pygame
from os.path import join

HOST = "0.0.0.0"
PORT = 5555
MAX_PLAYERS = 4
MIN_PLAYERS = 2

# Estado global del juego
game_state = {
    "status": "waiting",  # waiting, ready, running, finished
    "players": {},
    "meteors": [],
    "num_players": 0
}

lock = threading.Lock()
clients = []
player_count = 0

game_started = False


def broadcast_state():
    """Envía el estado del juego a todos los clientes"""
    state_message = {"type": "state", "state": game_state}
    message = (json.dumps(state_message) + "\n").encode("utf-8")

    with lock:
        disconnected = []
        for client_socket in clients:
            try:
                client_socket.sendall(message)
            except:
                disconnected.append(client_socket)

        for client_socket in disconnected:
            if client_socket in clients:
                clients.remove(client_socket)


def handle_client(conn, addr):
    """Maneja la conexión de un cliente individual"""
    global player_count
    player_id = -1

    try:
        with lock:
            if len(game_state["players"]) >= MAX_PLAYERS:
                conn.close()
                return

            player_count += 1
            player_id = player_count

            game_state["players"][player_id] = {
                "id": player_id,
                "username": f"Player{player_id}",
                "x": 500,
                "y": 500,
                "lives": 3,
                "score": 0,
                "alive": True
            }
            game_state["num_players"] = len(game_state["players"])

        print(f"Jugador {player_id} conectado desde {addr}")

        # Enviar mensaje de bienvenida
        welcome = {"type": "welcome", "player_id": player_id}
        conn.sendall((json.dumps(welcome) + "\n").encode("utf-8"))
        broadcast_state()

        with lock:
            if game_state["num_players"] >= MIN_PLAYERS:
                game_state["status"] = "ready"
                print(f"¡{game_state['num_players']} jugadores conectados! Esperando señal de inicio...")

        # Procesar mensajes del cliente
        conn_file = conn.makefile(mode="r")
        for line in conn_file:
            try:
                msg = json.loads(line.strip())
                action = msg.get("action")

                with lock:
                    if player_id not in game_state["players"]:
                        continue

                    pdata = game_state["players"][player_id]

                    if action == "join":
                        pdata["username"] = msg.get("username", f"Player{player_id}")
                    elif action == "update_position":
                        pdata["x"] = msg.get("x")
                        pdata["y"] = msg.get("y")
                    elif action == "update_score":
                        pdata["score"] = msg.get("score")
                    elif action == "hit":
                        pdata["lives"] -= 1
                        if pdata["lives"] <= 0:
                            pdata["alive"] = False
                            # Verificar si el juego terminó
                            alive_players = [p for p in game_state["players"].values() if p["alive"]]
                            if len(alive_players) == 0:
                                game_state["status"] = "finished"
                    elif action == "restart":
                        pdata["lives"] = 3
                        pdata["score"] = 0
                        pdata["alive"] = True
                        # Verificar si todos están listos para reiniciar
                        all_alive = all(p["alive"] for p in game_state["players"].values())
                        if all_alive:
                            game_state["status"] = "running"

                broadcast_state()

            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"Error con jugador {player_id}: {e}")
    finally:
        with lock:
            if player_id in game_state["players"]:
                del game_state["players"][player_id]
                game_state["num_players"] = len(game_state["players"])
        conn.close()
        print(f"Jugador {player_id} desconectado")
        broadcast_state()


def start_server_thread():
    """Inicia el servidor en un hilo separado"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)
    print(f"Servidor iniciado en {HOST}:{PORT}")
    print(f"Esperando hasta {MAX_PLAYERS} jugadores...")

    while True:
        conn, addr = server.accept()
        with lock:
            clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


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


def draw_button(screen, rect, text, font, hovered, active=True):
    """Dibuja un botón moderno con efectos"""
    if not active:
        color = (80, 80, 100)
        border_color = (120, 120, 140)
    else:
        color = (80, 220, 150) if hovered else (60, 180, 120)
        border_color = (255, 255, 255) if hovered else (200, 200, 200)

    # Sombra
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)

    # Botón principal
    pygame.draw.rect(screen, color, rect, border_radius=15)

    # Borde
    pygame.draw.rect(screen, border_color, rect, 4, border_radius=15)

    # Texto
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def draw_status_indicator(screen, x, y, status):
    """Dibuja un indicador de estado con color"""
    colors = {
        "waiting": (255, 200, 100),
        "ready": (100, 200, 255),
        "running": (100, 255, 150),
        "finished": (255, 100, 100)
    }

    color = colors.get(status, (150, 150, 150))

    # Círculo pulsante
    pulse = 1 + 0.2 * abs((pygame.time.get_ticks() / 500) % 2 - 1)
    radius = int(8 * pulse)
    pygame.draw.circle(screen, color, (x, y), radius)
    pygame.draw.circle(screen, (255, 255, 255), (x, y), radius, 2)


def run_server_gui():
    """Ejecuta la interfaz gráfica del servidor mejorada"""
    global game_started

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Space Shooter Server")
    clock = pygame.time.Clock()

    # Fuentes
    title_font = pygame.font.Font(None, 70)
    font = pygame.font.Font(None, 45)
    small_font = pygame.font.Font(None, 32)
    info_font = pygame.font.Font(None, 28)

    start_button_rect = pygame.Rect(250, 480, 300, 80)

    # Animación de partículas
    particles = []
    for i in range(20):
        particles.append({
            "x": (i * 40) % 800,
            "y": (i * 30) % 600,
            "speed": 20 + (i % 5) * 10
        })

    running = True
    animation_time = 0

    while running:
        dt = clock.tick(60) / 1000
        animation_time += dt

        mouse_pos = pygame.mouse.get_pos()
        button_hovered = start_button_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_hovered and game_state["num_players"] >= MIN_PLAYERS and not game_started:
                    # Iniciar el juego
                    with lock:
                        game_state["status"] = "running"
                        game_started = True
                    broadcast_state()
                    print("¡Juego iniciado!")

        # Fondo con gradiente
        draw_gradient_background(screen, (20, 25, 40), (40, 45, 70))

        # Partículas de fondo
        for particle in particles:
            particle["y"] = (particle["y"] + particle["speed"] * dt) % 600
            size = 2 + (particle["speed"] // 20)
            alpha = 150
            pygame.draw.circle(screen, (255, 255, 255, alpha),
                               (int(particle["x"]), int(particle["y"])), size)

        # Panel principal
        main_panel_rect = pygame.Rect(50, 50, 700, 380)
        draw_panel(screen, main_panel_rect, (30, 35, 55), 240)

        # Título con efecto
        title = title_font.render("SERVER CONTROL", True, (100, 200, 255))
        title_shadow = title_font.render("SERVER CONTROL", True, (50, 100, 150))
        title_rect = title.get_rect(center=(400, 100))
        screen.blit(title_shadow, title_rect.move(3, 3))
        screen.blit(title, title_rect)

        # Información del servidor
        server_panel_rect = pygame.Rect(80, 150, 640, 60)
        draw_panel(screen, server_panel_rect, (40, 50, 80), 200)

        server_info = info_font.render(f"Host: {HOST}:{PORT}", True, (200, 220, 255))
        screen.blit(server_info, (100, 165))

        # Indicador de estado
        status = game_state.get("status", "waiting")
        draw_status_indicator(screen, 620, 180, status)

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
            filled_width = int((num_players / MAX_PLAYERS) * progress_width)
            filled_rect = pygame.Rect(450, 245, filled_width, 30)

            # Color según el progreso
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

            list_title = small_font.render("Connected Players:", True, (180, 200, 255))
            screen.blit(list_title, (100, 320))

            y_offset = 355
            x_offset = 120
            col = 0

            for player_id, pdata in game_state.get("players", {}).items():
                username = pdata.get("username", f"Player{player_id}")
                lives = pdata.get("lives", 3)
                score = pdata.get("score", 0)
                alive = pdata.get("alive", True)

                # Color según estado
                if alive:
                    name_color = (150, 255, 150)
                    icon = "●"
                else:
                    name_color = (255, 100, 100)
                    icon = "○"

                player_text = info_font.render(f"{icon} {username}", True, name_color)
                screen.blit(player_text, (x_offset, y_offset))

                stats_text = info_font.render(f"({score} pts, ❤{lives})", True, (200, 200, 200))
                screen.blit(stats_text, (x_offset + 150, y_offset))

                col += 1
                if col % 2 == 0:
                    y_offset += 35
                    x_offset = 120
                else:
                    x_offset = 420

        # Botón de inicio o mensaje de estado
        if game_state["num_players"] >= MIN_PLAYERS and not game_started:
            draw_button(screen, start_button_rect, "START GAME", font, button_hovered, True)
        elif game_state["status"] == "running":
            status_panel = pygame.Rect(250, 480, 300, 80)
            draw_panel(screen, status_panel, (50, 150, 100), 220)
            status_msg = small_font.render("Game Running...", True, (150, 255, 150))
            status_rect = status_msg.get_rect(center=status_panel.center)
            screen.blit(status_msg, status_rect)
        elif game_state["status"] == "finished":
            status_panel = pygame.Rect(250, 480, 300, 80)
            draw_panel(screen, status_panel, (150, 50, 50), 220)
            status_msg = small_font.render("Game Finished", True, (255, 150, 150))
            status_rect = status_msg.get_rect(center=status_panel.center)
            screen.blit(status_msg, status_rect)
        else:
            status_panel = pygame.Rect(200, 480, 400, 80)
            draw_panel(screen, status_panel, (80, 80, 100), 220)

            if num_players == 0:
                msg = "Waiting for players..."
            else:
                msg = f"Need {MIN_PLAYERS - num_players} more player(s)"

            status_msg = small_font.render(msg, True, (200, 200, 200))
            status_rect = status_msg.get_rect(center=status_panel.center)

            # Texto parpadeante
            if pygame.time.get_ticks() % 1000 < 500:
                screen.blit(status_msg, status_rect)

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    # Iniciar servidor en hilo separado
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()

    # Ejecutar interfaz gráfica
    run_serve