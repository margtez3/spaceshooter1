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
            if game_state["num_players"] == MAX_PLAYERS:
                game_state["status"] = "ready"
                print(f"¡Todos los jugadores conectados! Esperando señal de inicio...")

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


def run_server_gui():
    """Ejecuta la interfaz gráfica del servidor"""
    global game_started

    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Servidor - Space Shooter")
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 40)
    small_font = pygame.font.Font(None, 30)

    # Botón de inicio
    start_button_rect = pygame.Rect(200, 250, 200, 60)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        button_hovered = start_button_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_hovered and game_state["status"] == "ready" and not game_started:
                    # Iniciar el juego
                    with lock:
                        game_state["status"] = "running"
                        game_started = True
                    broadcast_state()
                    print("¡Juego iniciado!")

        # Dibujar pantalla
        screen.fill((30, 30, 50))

        # Título
        title = font.render("SERVIDOR", True, (255, 255, 255))
        screen.blit(title, (220, 50))

        # Estado de conexión
        num_players = game_state.get("num_players", 0)
        status_text = small_font.render(f"Jugadores conectados: {num_players}/{MAX_PLAYERS}", True, (200, 200, 200))
        screen.blit(status_text, (150, 130))

        # Mostrar nombres de jugadores
        y_offset = 170
        for player_id, pdata in game_state.get("players", {}).items():
            username = pdata.get("username", f"Player{player_id}")
            player_text = small_font.render(f"- {username}", True, (150, 255, 150))
            screen.blit(player_text, (220, y_offset))
            y_offset += 30

        # Botón de inicio
        if game_state["status"] == "ready" and not game_started:
            button_color = (100, 255, 100) if button_hovered else (50, 200, 50)
            pygame.draw.rect(screen, button_color, start_button_rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), start_button_rect, 3, border_radius=10)
            button_text = font.render("START", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=start_button_rect.center)
            screen.blit(button_text, text_rect)
        elif game_state["status"] == "running":
            status = small_font.render("Juego en curso...", True, (100, 255, 100))
            screen.blit(status, (200, 280))
        elif game_state["status"] == "finished":
            status = small_font.render("Juego terminado", True, (255, 100, 100))
            screen.blit(status, (200, 280))
        else:
            status = small_font.render("Esperando jugadores...", True, (200, 200, 200))
            screen.blit(status, (180, 280))

        pygame.display.update()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    # Iniciar servidor en hilo separado
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()

    # Ejecutar interfaz gráfica
    run_server_gui()


