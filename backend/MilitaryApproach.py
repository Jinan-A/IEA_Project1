import socketio
from flask import Flask
import eventlet

app = Flask(__name__)
sio = socketio.Server(cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app)

GRID_SIZE = 10
AGENT_COUNT = 20

TARGET_SHAPE = [
    (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7),
    (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6),
    (3, 5), (4, 5), (5, 5), (6, 5),
    (4, 4), (5, 4)
]

def initialize_agents():
    return [{
        "x": i % GRID_SIZE,
        "y": GRID_SIZE - 2 + (i // GRID_SIZE),
        "target": TARGET_SHAPE[i]
    } for i in range(AGENT_COUNT)]

agents = initialize_agents()

def reset_agents():
    global agents
    agents = initialize_agents()
    sio.emit("agents_update", agents)

@sio.event
def connect(sid, environ):
    sio.emit("agents_update", agents)

@sio.on("start_formation")
def handle_start_formation(sid):
    batch_size = 1
    current_idx = 0
    active_agents = []

    while current_idx < AGENT_COUNT or len(active_agents) > 0:
        # Add new batch of agents
        if current_idx < AGENT_COUNT:
            next_batch = list(range(current_idx, min(current_idx + batch_size, AGENT_COUNT)))
            active_agents.extend(next_batch)
            current_idx += batch_size
            batch_size += 1

        # Move all active agents
        still_moving = []
        for agent_idx in active_agents:
            agent = agents[agent_idx]
            tx, ty = agent["target"]
            
            # Update X position
            if agent["x"] < tx:
                agent["x"] += 1
            elif agent["x"] > tx:
                agent["x"] -= 1
                
            # Update Y position
            if agent["y"] < ty:
                agent["y"] += 1
            elif agent["y"] > ty:
                agent["y"] -= 1
                
            # Keep moving if not at target
            if not (agent["x"] == tx and agent["y"] == ty):
                still_moving.append(agent_idx)

        active_agents = still_moving
        sio.emit("agents_update", agents)
        eventlet.sleep(0.5)

@sio.on("reset_formation")
def handle_reset_formation(sid):
    reset_agents()

@sio.event
def disconnect(sid):
    pass

if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)