"""
Módulo de comunicación cliente-servidor
Maneja el envío y recepción de datos entre el cliente y el servidor
"""

import socket
import pickle


class Network:
    """Clase para manejar la comunicación de red"""

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ""
        self.port = 5555
        self.addr = ("", 0)
        self.player_id = None
        self.connected = False
        self.last_error = ""

    def connect(self, server_ip, server_port):
        """Conecta al servidor y recibe el ID del jugador"""
        try:
            if server_ip.lower() == "localhost":
                server_ip = "127.0.0.1"

            self.server = server_ip
            self.port = int(server_port)
            self.addr = (self.server, self.port)

            self.client.settimeout(10)  # Timeout más largo para conexiones remotas
            self.client.connect(self.addr)
            self.client.settimeout(None)  # Remove timeout after connection

            # Recibir ID del jugador
            data = self.client.recv(4096)
            message = pickle.loads(data)

            if message['type'] == 'player_id':
                self.player_id = message['id']
                self.connected = True
                return True, self.player_id
            elif message['type'] == 'error':
                self.last_error = message['message']
                return False, message['message']
        except socket.gaierror as e:
            self.last_error = f"No se pudo resolver la dirección: {server_ip}"
            return False, self.last_error
        except socket.timeout:
            self.last_error = "Tiempo de conexión agotado. Verifica la URL de ngrok."
            return False, self.last_error
        except ConnectionRefusedError:
            self.last_error = "Conexión rechazada. Verifica que el servidor esté ejecutándose."
            return False, self.last_error
        except Exception as e:
            self.last_error = f"Error de conexión: {str(e)}"
            return False, self.last_error

        return False, "Error desconocido"

    def send(self, data):
        """Envía datos al servidor y recibe la respuesta"""
        try:
            self.client.send(pickle.dumps(data))
            response = self.client.recv(8192)
            return pickle.loads(response)
        except Exception as e:
            print(f"[ERROR] Error enviando datos: {e}")
            return None

    def disconnect(self):
        """Cierra la conexión con el servidor"""
        try:
            self.client.close()
            self.connected = False
        except:
            pass

    def send_name(self, name):
        """Envía el nombre del jugador al servidor"""
        try:
            self.client.send(pickle.dumps({'type': 'set_name', 'name': name}))
            # Wait for confirmation
            data = self.client.recv(4096)
            response = pickle.loads(data)
            return response.get('type') == 'name_confirmed'
        except Exception as e:
            print(f"[ERROR] Error enviando nombre: {e}")
            return False
