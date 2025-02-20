import random
import socketio
from flask import Flask
import eventlet

app = Flask(__name__)
sio = socketio.Server(cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app)

GRID_SIZE = 10
AGENT_COUNT = 20

# Function to initialize agents at the starting position
def initialize_agents():
    return [
        {"x": i % GRID_SIZE, "y": GRID_SIZE - 2 + (i // GRID_SIZE), "target": None}
        for i in range(AGENT_COUNT)
    ]

agents = initialize_agents()

# Target shape coordinates (relative to a 10x10 grid)
TARGET_SHAPE = [
    (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7),
    (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6),
    (3, 5), (4, 5), (5, 5), (6, 5),
    (4, 4), (5, 4)
]

def heuristic(agent, target):
    """Compute Manhattan Distance heuristic."""
    return abs(agent["x"] - target[0]) + abs(agent["y"] - target[1])

def move_agents():
    """Move agents toward the target shape using a heuristic search."""
    global agents
    assigned_targets = list(TARGET_SHAPE)  # Copy of the target shape positions

    for i in range(len(agents)):
        if assigned_targets:
            target = assigned_targets.pop(0)  # Assign each agent a target
            min_distance = heuristic(agents[i], target)

            # Move agent towards target (Greedy approach)
            if agents[i]["x"] < target[0]: agents[i]["x"] += 1
            elif agents[i]["x"] > target[0]: agents[i]["x"] -= 1

            if agents[i]["y"] < target[1]: agents[i]["y"] += 1
            elif agents[i]["y"] > target[1]: agents[i]["y"] -= 1

    sio.emit("agents_update", agents)  # Send updated positions to clients

def reset_agents():
    """Reset agents to the initial starting position."""
    global agents
    agents = initialize_agents()
    sio.emit("agents_update", agents)  # Send reset state to clients

@sio.event
def connect(sid, environ):
    print(f"Client {sid} connected")
    sio.emit("agents_update", agents)

@sio.on("start_formation")
def handle_start_formation(sid):
    """Start heuristic search to move agents into shape."""
    for _ in range(20):  # Move iteratively until formation is reached
        move_agents()
        eventlet.sleep(0.5)  # Add delay for visualization

@sio.on("reset_formation")
def handle_reset_formation(sid):
    """Reset the agents to their initial positions."""
    print(f"Client {sid} requested a reset")
    reset_agents()

@sio.event
def disconnect(sid):
    print(f"Client {sid} disconnected")

if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)
