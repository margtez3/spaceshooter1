"""
Archivo con la clase Player.

Maneja toda la lógica del jugador: movimiento, disparo de láseres,
y cooldown entre disparos.
"""

import pygame
from os.path import join
from laser import Laser


class Player(pygame.sprite.Sprite):
    """
    Clase que representa al jugador en el juego.

    El jugador puede moverse en 8 direcciones usando las flechas del teclado
    y disparar láseres con la barra espaciadora. Tiene un cooldown entre disparos
    para evitar spam.

    Atributos:
        og: Imagen original del jugador
        image: Imagen actual del jugador
        rect: Rectángulo que define posición y colisiones
        direction: Vector de dirección del movimiento
        speed: Velocidad de movimiento en píxeles por segundo
        can_shoot: Boolean que indica si puede disparar
        laser_shoot_time: Timestamp del último disparo
        cooldown_duration: Tiempo de espera entre disparos en milisegundos
    """

    def __init__(self, groups, screen_width, screen_height, laser_surf,
                 all_sprites, laser_sprites, laser_sound, player_id=1):
        """
        Inicializa el jugador con su imagen, posición y configuración.

        Argumentos:
            groups: Grupos de sprites a los que pertenece
            screen_width: Ancho de la pantalla
            screen_height: Alto de la pantalla
            laser_surf: Superficie de la imagen del láser
            all_sprites: Grupo con todos los sprites del juego
            laser_sprites: Grupo específico de láseres
            laser_sound: Sonido que se reproduce al disparar
            player_id: ID del jugador (1-4) para seleccionar la imagen correcta
        """
        super().__init__(groups)

        # Diccionario que mapea IDs de jugador a sus imágenes
        player_images = {
            1: 'player.png',
            2: 'player2.png',
            3: 'player3.png',
            4: 'player4.png'
        }

        # Seleccionamos la imagen según el ID del jugador
        image_name = player_images.get(player_id, 'player.png')

        # Cargamos la imagen y la convertimos para mejor rendimiento
        self.og = pygame.image.load(join('images', image_name)).convert_alpha()
        self.image = self.og

        # Posicionamos al jugador en el centro de la pantalla
        self.rect = self.image.get_rect(center=(screen_width / 2, screen_height / 2))

        # Vector de dirección (empieza en 0,0 = sin movimiento)
        self.direction = pygame.math.Vector2()
        self.speed = 300  # Píxeles por segundo

        # Guardamos referencias para crear láseres
        self.laser_surf = laser_surf
        self.all_sprites = all_sprites
        self.laser_sprites = laser_sprites
        self.laser_sound = laser_sound

        # Sistema de cooldown para disparos
        self.can_shoot = True  # Puede disparar al inicio
        self.laser_shoot_time = 0  # Timestamp del último disparo
        self.cooldown_duration = 400  # 400ms entre disparos

    def laser_timer(self):
        """
        Maneja el cooldown entre disparos.

        Verifica si ha pasado suficiente tiempo desde el último disparo
        para permitir disparar de nuevo. Se llama en cada frame.
        """
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()  # Tiempo actual en ms
            # Si ya pasó el tiempo de cooldown, permitimos disparar
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt, events):
        """
        Actualiza el estado del jugador cada frame.

        Argumentos:
            dt: Delta time (tiempo transcurrido desde el último frame en segundos)
            events: Lista de eventos de pygame del frame actual

        Maneja el movimiento del jugador y los disparos.
        """
        # Obtenemos el estado de las teclas presionadas
        keys = pygame.key.get_pressed()

        # Calculamos la dirección del movimiento
        # int() convierte True/False a 1/0
        # Restamos para obtener -1, 0 o 1 en cada eje
        self.direction.x = int(keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN] - keys[pygame.K_UP])

        # Normalizamos el vector para que el movimiento diagonal no sea más rápido
        # Si el vector es (0,0), lo dejamos así
        self.direction = self.direction.normalize() if self.direction else self.direction

        # Actualizamos la posición multiplicando dirección * velocidad * tiempo
        self.rect.center += self.direction * self.speed * dt

        # Procesamos eventos para detectar disparos
        for event in events:
            # Si presionan espacio y pueden disparar
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.can_shoot:
                # Creamos un nuevo láser en la posición superior del jugador
                Laser([self.all_sprites, self.laser_sprites], self.laser_surf, self.rect.midtop)
                self.can_shoot = False  # Activamos el cooldown
                self.laser_shoot_time = pygame.time.get_ticks()  # Guardamos el tiempo
                self.laser_sound.play()  # Reproducimos el sonido

        # Actualizamos el timer del cooldown
        self.laser_timer()
