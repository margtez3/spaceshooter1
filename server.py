"""
Servidor multijugador para Space Shooter
Ejecuta este archivo primero antes de iniciar los clientes
Si usas ngrok, ejecuta: ngrok tcp 5555
"""

import socket
import threading
import pickle
import time
from random import randint

# Configuración del servidor
HOST = '0.0.0.0'  # Escucha en todas las interfaces
PORT = 5555
MAX_PLAYERS = 2

# Estado del juego compartido
game_state = {
    'players': {},  # {player_id: {'x': x, 'y': y, 'alive': True}}
    'meteors': [],  # [{'x': x, 'y': y, 'id': id, 'rotation': rot}]
    'lasers': [],  # [{'x': x, 'y': y, 'id': id, 'player_id': pid}]
    'scores': {1: 0, 2: 0},
    'game_started': False,
    'meteor_counter': 0,
    'laser_counter': 0
}

# Lock para sincronización de hilos
game_lock = threading.Lock()

# Lista de conexiones de clientes
clients = []
player_count = 0


def handle_client(conn, addr, player_id):
    """Maneja la comunicación con un cliente específico"""
    global game_state, player_count

    print(f"[NUEVA CONEXIÓN] Jugador {player_id} conectado desde {addr}")

    # Enviar el ID del jugador al cliente
    try:
        conn.send(pickle.dumps({'type': 'player_id', 'id': player_id}))
    except:
        print(f"[ERROR] No se pudo enviar ID al jugador {player_id}")
        return

    # Inicializar jugador en el estado del juego
    with game_lock:
        game_state['players'][player_id] = {
            'x': 640 if player_id == 1 else 640,
            'y': 400 if player_id == 1 else 400,
            'alive': True
        }

    connected = True
    while connected:
        try:
            # Recibir datos del cliente
            data = conn.recv(4096)
            if not data:
                break

            message = pickle.loads(data)

            # Procesar diferentes tipos de mensajes
            if message['type'] == 'update_position':
                with game_lock:
                    if player_id in game_state['players']:
                        game_state['players'][player_id]['x'] = message['x']
                        game_state['players'][player_id]['y'] = message['y']

            elif message['type'] == 'shoot_laser':
                with game_lock:
                    game_state['laser_counter'] += 1
                    game_state['lasers'].append({
                        'x': message['x'],
                        'y': message['y'],
                        'id': game_state['laser_counter'],
                        'player_id': player_id
                    })

            elif message['type'] == 'player_died':
                with game_lock:
                    if player_id in game_state['players']:
                        game_state['players'][player_id]['alive'] = False

            elif message['type'] == 'start_game':
                with game_lock:
                    game_state['game_started'] = True

            # Enviar el estado actualizado del juego al cliente
            with game_lock:
                conn.send(pickle.dumps(game_state))

        except Exception as e:
            print(f"[ERROR] Error con jugador {player_id}: {e}")
            break

    # Limpiar cuando el cliente se desconecta
    print(f"[DESCONEXIÓN] Jugador {player_id} desconectado")
    with game_lock:
        if player_id in game_state['players']:
            del game_state['players'][player_id]

    conn.close()
    clients.remove(conn)
    player_count -= 1


def spawn_meteors():
    """Hilo que genera meteoros periódicamente"""
    global game_state

    while True:
        time.sleep(0.5)  # Generar meteoro cada 0.5 segundos

        with game_lock:
            if game_state['game_started'] and len(game_state['players']) > 0:
                game_state['meteor_counter'] += 1
                game_state['meteors'].append({
                    'x': randint(0, 1280),
                    'y': randint(-200, -100),
                    'id': game_state['meteor_counter'],
                    'rotation': 0,
                    'dir_x': (randint(-50, 50) / 100),
                    'dir_y': 1,
                    'speed': randint(400, 500),
                    'rot_speed': randint(50, 80),
                    'spawn_time': time.time()
                })


def update_game_state():
    """Hilo que actualiza el estado del juego (meteoros, colisiones, etc.)"""
    global game_state

    while True:
        time.sleep(0.016)  # ~60 FPS

        with game_lock:
            current_time = time.time()

            # Actualizar meteoros
            meteors_to_remove = []
            for meteor in game_state['meteors']:
                # Actualizar posición
                meteor['y'] += meteor['speed'] * 0.016
                meteor['x'] += meteor['dir_x'] * meteor['speed'] * 0.016
                meteor['rotation'] += meteor['rot_speed'] * 0.016

                # Eliminar meteoros viejos (más de 5 segundos o fuera de pantalla)
                if current_time - meteor['spawn_time'] > 5 or meteor['y'] > 900:
                    meteors_to_remove.append(meteor)

                for player_id, player_data in game_state['players'].items():
                    if player_data.get('alive', True):
                        # Calcular distancia entre meteoro y jugador
                        dx = meteor['x'] - player_data['x']
                        dy = meteor['y'] - player_data['y']
                        distance = (dx * dx + dy * dy) ** 0.5

                        # Radio de colisión ~50 píxeles
                        if distance < 50:
                            # Marcar jugador como muerto
                            game_state['players'][player_id]['alive'] = False
                            # Marcar meteoro para eliminar
                            if meteor not in meteors_to_remove:
                                meteors_to_remove.append(meteor)

            for meteor in meteors_to_remove:
                if meteor in game_state['meteors']:
                    game_state['meteors'].remove(meteor)

            lasers_to_remove = []
            meteors_to_remove = []

            for laser in game_state['lasers']:
                laser['y'] -= 400 * 0.016  # Mover láser hacia arriba

                # Eliminar láseres que salen de la pantalla
                if laser['y'] < 0:
                    lasers_to_remove.append(laser)
                    continue

                # Detectar colisión con meteoros
                for meteor in game_state['meteors']:
                    # Calcular distancia entre láser y meteoro
                    dx = laser['x'] - meteor['x']
                    dy = laser['y'] - meteor['y']
                    distance = (dx * dx + dy * dy) ** 0.5

                    # Radio de colisión ~40 píxeles
                    if distance < 40:
                        # Incrementar puntaje del jugador que disparó
                        player_id = laser['player_id']
                        if player_id in game_state['scores']:
                            game_state['scores'][player_id] += 1

                        # Marcar láser y meteoro para eliminar
                        if laser not in lasers_to_remove:
                            lasers_to_remove.append(laser)
                        if meteor not in meteors_to_remove:
                            meteors_to_remove.append(meteor)
                        break

            # Eliminar láseres y meteoros marcados
            for laser in lasers_to_remove:
                if laser in game_state['lasers']:
                    game_state['lasers'].remove(laser)

            for meteor in meteors_to_remove:
                if meteor in game_state['meteors']:
                    game_state['meteors'].remove(meteor)


def start_server():
    """Inicia el servidor y acepta conexiones de clientes"""
    global player_count

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)

    print(f"[SERVIDOR INICIADO] Escuchando en {HOST}:{PORT}")
    print(f"[INFO] Esperando hasta {MAX_PLAYERS} jugadores...")
    print(f"[INFO] Si usas ngrok, ejecuta: ngrok tcp {PORT}")

    # Iniciar hilos para actualizar el juego
    meteor_thread = threading.Thread(target=spawn_meteors, daemon=True)
    meteor_thread.start()

    update_thread = threading.Thread(target=update_game_state, daemon=True)
    update_thread.start()

    # Aceptar conexiones de clientes
    while True:
        conn, addr = server.accept()

        if player_count < MAX_PLAYERS:
            player_count += 1
            player_id = player_count
            clients.append(conn)

            # Crear un hilo para manejar este cliente
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, player_id),
                daemon=True
            )
            client_thread.start()

            print(f"[CONEXIONES ACTIVAS] {player_count}/{MAX_PLAYERS}")
        else:
            # Rechazar conexión si ya hay suficientes jugadores
            print(f"[RECHAZADO] Conexión desde {addr} - Servidor lleno")
            conn.send(pickle.dumps({'type': 'error', 'message': 'Servidor lleno'}))
            conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR SPACE SHOOTER MULTIJUGADOR")
    print("=" * 50)
    start_server()
