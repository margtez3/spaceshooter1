# Space Shooter Multiplayer

Space Shooter Multiplayer is a 2D multiplayer arcade-style video game developed in Python using Pygame.  
The project implements real-time communication through a client–server architecture based on TCP sockets, enabling synchronized gameplay between multiple players.

This project was built with an academic and technical focus, emphasizing clean code structure, networking fundamentals, and interactive system design.

---

## Project Overview

- 2D arcade-style video game
- Real-time multiplayer support
- Client–server architecture
- Player state synchronization (position, lives, score)
- Graphical interface for both game client and server

Each player controls a spaceship that must avoid and destroy falling meteors to score points.  
The match ends when all players lose their lives, displaying a final leaderboard.

---

## Key Features

- Smooth eight-directional movement
- Shooting system with cooldown control
- Pixel-perfect collision detection
- Enemies with randomized movement and rotation
- Life and scoring system
- Multiplayer leaderboard on game over
- Synchronized game restart
- Server-side graphical control panel

---

## Architecture and Design

The project is organized into modular components to improve readability, maintainability, and scalability:

- `main.py`: Game client and main loop
- `server.py`: Multiplayer server managing global game state
- `network.py`: Client–server communication (TCP + JSON)
- `player.py`: Player logic and controls
- `meteor.py`: Enemy logic
- `laser.py`: Shooting system
- `star.py`: Background decorative elements

Communication between clients and the server is handled using JSON messages, allowing a clear separation between gameplay logic and network synchronization.

---

## Technologies Used

- Python 3
- Pygame
- TCP Sockets
- JSON
- Threading (concurrent programming)
- Object-Oriented Programming (OOP)

---

## Running the Project

### Start the server

```bash
python server.py

```

### Start the client

```bash
python main.py

```

### Key Learnings

- Design and implementation of real-time multiplayer systems
- Client–server communication using TCP sockets
- State synchronization and concurrency management
- 2D game development with Pygame
- Modular software architecture in Python

### Author 
Mariana Gutiérrez Yáñez
Academic project – Multiplayer game development in Python






