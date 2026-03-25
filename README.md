(this README is mostly LLM generated, and should not be taken as gospel.)

# AiMO Game Prototype

A 2D top-down multiplayer social/educational platform game prototype built in Godot 4.6. A **Teacher** hosts a session, students join and move freely through tile-based rooms, and the teacher can launch activities that teleport everyone to a shared space.

> **This is an early prototype.** Most room gameplay logic is stubbed with `TODO` comments, and teacher/student role enforcement is wired up but not yet fully implemented. There is plenty of room to contribute.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Running Locally](#running-locally)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Key Concepts](#key-concepts)
- [Where to Contribute](#where-to-contribute)

---

## Overview

The game uses an **authoritative server** model over WebSockets. All game-world mutations (spawning, moving, despawning) happen server-side; clients only send input and receive state. Each connecting player is given a private personal room. A shared Lobby room is always present and is used as the destination when a teacher launches an activity.

The aesthetic borrows from the Portal universe (Chell character sprites, Companion Cube, surveillance cameras), but the core concept is an interactive educational platform.

**Tech stack:**

- **Engine**: Godot 4.6 (GDScript only, no external dependencies)
- **Renderer**: GL Compatibility (supports mobile/web targets)
- **Networking**: Godot built-in `WebSocketMultiplayerPeer`, port 80
- **Physics**: Godot built-in 2D physics

---

## Getting Started

### Prerequisites

- [Godot 4.6](https://godotengine.org/download/) — the standard (non-Mono) build is sufficient.
- No additional tools or package managers are required.

### Clone and open

```bash
git clone <repo-url>
```

Open **Godot 4.6**, click **Import**, and select the `project.godot` file from the cloned folder.

---

## Running Locally

Once you've opened the project in the Godot editor, set the number of run isntances to at least 2 from **Debug -> Customize Run Instances...**

This will allow you to set one instance as the server, and the rest as clients afterward, when running the project with F5.

Alternatively, you can export a dedicated server build, run it as an executable, and then run the client either from the editor or as a web export. Web exports must be served through an HTTP(S) server, for example with ```python3 -m http.server 80```.

---

## Project Structure

```
aimo_game_proto/
├── main.gd / main.tscn          # Root scene — core RPC logic, spawning, room management
├── autoloads/
│   ├── network_handler.gd       # Singleton — creates WebSocket server or client peer
│   └── signal_bus.gd            # Singleton — global signal hub for decoupled communication
├── player/
│   └── player.gd                # CharacterBody2D — movement, animation, pushing movables
├── rooms/
│   ├── personal_room.gd         # Per-player private room (tracks owner username/peer ID)
│   └── shared_room_1.gd         # Shared Lobby room
├── npcs/
│   └── tall_button.gd           # Interactive NPC: animation, HTTP request, response display
├── items/
│   └── props/                   # Movable props (Companion Cube, surveillance camera)
├── misc/
│   ├── plot_marker.tscn         # Marker2D slots used to position personal rooms (16 in a grid)
│   └── server_camera.tscn       # Debug camera spawned server-side only
├── ui/
│   ├── loading/                 # Full-screen loading overlay
│   └── menus/
│       ├── debug_menu.gd        # Dev-only menu: server/client and teacher/student selection
│       └── pause_menu.gd        # In-game menu: room list, join room, launch activity
└── textures/                    # Sprite frames, spritesheets, tilesets
```

**Start reading here:** `main.gd` is the heart of the project. It handles player/room spawning, all server-side RPCs, and the startup branching logic for each platform mode.

---

## Architecture

### Authoritative server

Clients never write to the game world. When a client wants to do something (join a room, launch an activity), it calls an `@rpc` function on the server. The server validates and performs the action, and Godot's `MultiplayerSpawner` automatically replicates the resulting node changes to all clients.

```
Client                        Server
  |                              |
  |-- rpc("move_player_to_room") -->|
  |                              | validates, moves node
  |<-- MultiplayerSpawner sync --|
```

### MultiplayerSpawner

A single `MultiplayerSpawner` node lives at the root of the scene. When the server adds a `player.tscn`, `personal_room.tscn`, or `shared_room_1.tscn` as a child of `GameWorld`, the spawner automatically replicates that node to every connected client.

### Authority splitting

Each player node's `InputHandler` and `Camera2D` have their `multiplayer_authority` set to that player's peer ID. This means only the owning client processes input and drives the camera — all other peers see those nodes as read-only.

### Platform detection

`main.gd` branches at startup based on the export type:

| Export | Behaviour |
|---|---|
| `dedicated_server` | Auto-starts as server |
| `web` | Auto-connects as client |
| Desktop (editor / debug) | Shows the debug menu for manual role selection |

---

## Key Concepts

### Signal Bus (`autoloads/signal_bus.gd`)

A lightweight global event system. Instead of getting direct node references, systems emit and listen to signals here. If you add a new cross-system event, declare it in `signal_bus.gd`.

| Signal | When it fires |
|---|---|
| `started_loading` | Loading screen should appear |
| `finished_loading` | Loading screen should hide (1s delay) |
| `new_player_info_received` | Debug menu login complete — carries role + username |
| `activity_launched` | Teacher started an activity |
| `activity_ended` | Activity is over |
| `player_clicked_join_room` | Player selected a room from the pause menu |

### Global Groups

Nodes are tagged with groups so any script can query them without storing direct references:

| Group | Contains |
|---|---|
| `players` | All spawned player nodes |
| `rooms` | All room nodes |
| `personal_rooms` | Personal-room subset |
| `movables` | Physics props players can push |
| `npcs` | Interactive NPC nodes |

### Roles

| Role | Capabilities |
|---|---|
| **Teacher** | Can launch activities (teleports all players to the Lobby) |
| **Student** | Moves freely, joins rooms, interacts with NPCs |

Role enforcement is a known TODO — currently any peer can call teacher-only RPCs.

### Personal Rooms

When a player connects, `main.gd` finds a free `plot_marker` (one of 16 `Marker2D` nodes laid out in a grid), instantiates a `personal_room.tscn` at that position, and then spawns the player inside it. When the player disconnects, the room is freed and the plot marker slot is returned to the pool.

---

## Where to Contribute

Good starting points for new contributors:

- **Role enforcement** — `main.gd` has TODO comments where teacher-only actions should be gated behind a role check.
- **Room gameplay** — `rooms/personal_room.gd` and `rooms/shared_room_1.gd` are mostly stubs; the room logic is the main area waiting to be built out.
- **Character selection** — `player.gd`'s `apply_visuals()` currently hard-codes sprites by username. This should be replaced with a proper selection UI.
- **Public rooms** — `main.gd` has stubbed `add_public_room` / `remove_public_room` functions ready to be implemented.
- **NPC interactions** — `npcs/tall_button.gd` is a working proof-of-concept; new NPC types can follow the same pattern.