"""
Archivo que conecta main.py con el server.py.

Maneja la conexión con el servidor y el intercambio de datos usando
sockets TCP y JSON para la serialización de mensajes.

"""

import socket
import json
import threading


class Network:
    """
    Clase que maneja la comunicación de red del cliente con el servidor.

    Implementa un cliente TCP que se conecta al servidor del juego,
    envía actualizaciones del jugador local y recibe el estado global
    del juego en tiempo real.

    Atributos:
        client: Socket TCP para la conexión con el servidor
        connected: Boolean que indica si hay conexión activa
        player_id: ID único asignado por el servidor
        game_state: Diccionario con el estado actual del juego
        lock: Lock para sincronización de threads
    """

    def __init__(self):
        """
        Inicializa el cliente de red con valores por defecto.
        """
        # Creamos el socket TCP
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False  # No estamos conectados al inicio
        self.player_id = None  # El servidor nos asignará un ID

        # Estado inicial del juego (se actualizará al recibir datos)
        self.game_state = {
            "status": "waiting",
            "players": {},
            "meteors": [],
            "num_players": 0
        }

        # Lock para evitar que varios hilos cambien el estado del juego al mismo tiempo
        self.lock = threading.Lock()

    def connect(self, host, port, username):
        """
        Conecta al servidor y envía el nombre de usuario.

        Argumentos:
            host: Dirección IP o hostname del servidor
            port: Puerto del servidor
            username: Nombre de usuario del jugador

        Devuelve:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Intentamos conectar al servidor
            self.client.connect((host, int(port)))
            self.connected = True

            # Enviamos nuestro nombre de usuario
            self.send_data({"action": "join", "username": username})

            # Iniciamos un thread para recibir datos continuamente
            threading.Thread(target=self.receive_data, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def send_data(self, data):
        """
        Envía datos al servidor en formato JSON.

        Argumentos:
            data: Diccionario con los datos a enviar

        Los datos se serializan a JSON y se envían con un salto de línea
        al final para delimitar mensajes.
        """
        try:
            # Convertimos el diccionario a JSON y agregamos \n
            message = (json.dumps(data) + "\n").encode("utf-8")
            # Enviamos todo el mensaje
            self.client.sendall(message)
        except Exception as e:
            print(f"Error al enviar datos: {e}")
            self.connected = False

    def receive_data(self):
        """
        Recibe datos del servidor continuamente en un thread separado.

        Este método corre en un loop infinito recibiendo mensajes del servidor
        y actualizando el estado local del juego. Se ejecuta en un thread daemon
        para que termine automáticamente cuando el programa cierre.
        """
        try:
            # Creamos un file object para leer línea por línea
            file = self.client.makefile(mode="r")

            # Loop infinito para recibir mensajes
            for line in file:
                # Parseamos el JSON recibido
                data = json.loads(line.strip())
                msg_type = data.get("type")

                if msg_type == "welcome":
                    # El servidor nos asigna un ID
                    self.player_id = data.get("player_id")
                    print(f"Conectado como jugador {self.player_id}")

                elif msg_type == "state":
                    # Actualizamos el estado del juego de forma thread-safe
                    with self.lock:
                        self.game_state = data.get("state", {})

        except Exception as e:
            print(f"Conexión perdida: {e}")
            self.connected = False

    def send_position(self, x, y):
        """
        Envía la posición actual del jugador al servidor.

        Argumentos:
            x: Coordenada X del jugador
            y: Coordenada Y del jugador
        """
        self.send_data({
            "action": "update_position",
            "x": x,
            "y": y
        })

    def send_laser(self, x, y):
        """
        Envía información de disparo láser al servidor.

        Argumentos:
            x: Coordenada X donde se disparó
            y: Coordenada Y donde se disparó
        """
        self.send_data({
            "action": "shoot_laser",
            "x": x,
            "y": y
        })

    def send_hit(self):
        """
        Notifica al servidor que el jugador fue golpeado por un meteorito.

        El servidor reducirá las vidas del jugador y actualizará su estado.
        """
        self.send_data({
            "action": "hit"
        })

    def send_score(self, score):
        """
        Envía el puntaje actual del jugador al servidor.

        Argumentos:
            score: Puntaje actual del jugador
        """
        self.send_data({
            "action": "update_score",
            "score": score
        })

    def send_restart(self):
        """
        Notifica al servidor que el jugador quiere reiniciar el juego.

        El servidor reiniciará el estado del jugador y verificará si
        todos los jugadores están listos para comenzar de nuevo.
        """
        self.send_data({
            "action": "restart"
        })

    def get_game_state(self):
        """
        Obtiene una copia del estado actual del juego de forma thread-safe.

        Devuelve:
            dict: Copia del diccionario con el estado del juego

        Usamos un lock para evitar leer el estado mientras se está actualizando.
        """
        with self.lock:
            return self.game_state.copy()

    def disconnect(self):
        """
        Cierra la conexión con el servidor.
        """
        self.connected = False
        try:
            self.client.close()
        except:
            pass  # Ignoramos errores al cerrar
