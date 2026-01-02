Space Shooter Multiplayer

Space Shooter Multiplayer es un videojuego 2D desarrollado en Python con Pygame, que implementa un sistema multijugador en tiempo real mediante comunicación cliente–servidor usando sockets TCP.
El juego combina mecánicas clásicas de arcade con sincronización en red, permitiendo que varios jugadores compartan una misma partida.

 Descripción del juego

Cada jugador controla una nave espacial que se mueve libremente por la pantalla.
Desde la parte superior caen meteoritos que deben ser esquivados o destruidos usando láseres.

El objetivo es:

Sobrevivir el mayor tiempo posible

Destruir meteoritos para ganar puntos

Competir de manera cooperativa/competitiva con otros jugadores conectados

Cada jugador comienza con 3 vidas.
Cuando todos los jugadores pierden sus vidas, la partida termina y se muestra una tabla de puntuaciones.

 Modo multijugador (Cliente–Servidor)

El juego utiliza una arquitectura cliente–servidor:

 Servidor (server.py)

Administra hasta 4 jugadores

Mantiene el estado global del juego

Sincroniza posiciones, vidas y puntajes

Incluye una interfaz gráfica para monitorear la partida

 Cliente (main.py)

Se conecta al servidor mediante IP y puerto

Envía información del jugador (posición, impactos, puntaje)

Recibe el estado global para mostrar a los demás jugadores

La comunicación se realiza usando:

Sockets TCP

Mensajes en formato JSON

Tecnologías utilizadas

Python 3

Pygame

Sockets TCP

JSON

Threading (multihilo)

Cómo ejecutar el proyecto
Iniciar el servidor
python server.py


Esto abrirá una ventana con el panel de control del servidor.

Iniciar uno o más clientes
python main.py


En la pantalla de inicio:

Ingresa tu username

IP del servidor (por ejemplo 127.0.0.1)

Puerto (5555 por defecto)

Puedes ejecutar el cliente varias veces (o en distintas computadoras) para jugar en multijugador.

 Enfoque académico

Este proyecto demuestra conceptos clave de:

Programación orientada a objetos

Desarrollo de videojuegos 2D

Sistemas distribuidos

Comunicación en red

Manejo de concurrencia (threads)

Diseño de interfaces gráficas

Es ideal como:

Proyecto universitario

Práctica de redes

Base para extender a juegos más complejos

Posibles mejoras futuras

Sincronización de meteoritos desde el servidor

Chat entre jugadores

Power-ups

Niveles de dificultad

Animaciones del jugador

Persistencia de puntajes

 Autora

Mariana Gutiérrez Yáñez
Ingeniería en Software 
Proyecto académico – videojuego multijugador en Python
