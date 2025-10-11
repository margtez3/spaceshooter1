"""
Módulo de red para el juego de naves espaciales multijugador.
Maneja la conexión con el servidor y el intercambio de datos.
"""

import socket
import json
import threading


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.player_id = None
        self.game_state = {
            "status": "waiting",
            "players": {},
            "meteors": [],
            "num_players": 0
        }
        self.lock = threading.Lock()

    def connect(self, host, port, username):
        """Conecta al servidor y envía el nombre de usuario"""
        try:
            self.client.connect((host, int(port)))
            self.connected = True
            # Enviar nombre de usuario
            self.send_data({"action": "join", "username": username})
            # Iniciar hilo de escucha
            threading.Thread(target=self.receive_data, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def send_data(self, data):
        """Envía datos al servidor en formato JSON"""
        try:
            message = (json.dumps(data) + "\n").encode("utf-8")
            self.client.sendall(message)
        except Exception as e:
            print(f"Error al enviar datos: {e}")
            self.connected = False

    def receive_data(self):
        """Recibe datos del servidor continuamente"""
        try:
            file = self.client.makefile(mode="r")
            for line in file:
                data = json.loads(line.strip())
                msg_type = data.get("type")

                if msg_type == "welcome":
                    self.player_id = data.get("player_id")
                    print(f"Conectado como jugador {self.player_id}")
                elif msg_type == "state":
                    with self.lock:
                        self.game_state = data.get("state", {})
        except Exception as e:
            print(f"Conexión perdida: {e}")
            self.connected = False

    def send_position(self, x, y):
        """Envía la posición del jugador al servidor"""
        self.send_data({
            "action": "update_position",
            "x": x,
            "y": y
        })

    def send_laser(self, x, y):
        """Envía información de disparo láser"""
        self.send_data({
            "action": "shoot_laser",
            "x": x,
            "y": y
        })

    def send_hit(self):
        """Notifica al servidor que el jugador fue golpeado"""
        self.send_data({
            "action": "hit"
        })

    def send_score(self, score):
        """Envía el puntaje actual al servidor"""
        self.send_data({
            "action": "update_score",
            "score": score
        })

    def send_restart(self):
        """Notifica al servidor que el jugador quiere reiniciar"""
        self.send_data({
            "action": "restart"
        })

    def get_game_state(self):
        """Obtiene el estado actual del juego de forma segura"""
        with self.lock:
            return self.game_state.copy()

    def disconnect(self):
        """Cierra la conexión con el servidor"""
        self.connected = False
        try:
            self.client.close()
        except:
            pass
