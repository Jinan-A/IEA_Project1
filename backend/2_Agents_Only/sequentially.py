import socketio
from flask import Flask
import eventlet

app = Flask(__name__)
sio = socketio.Server(cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app)

GRID_SIZE = 10
AGENTS = [
    {"id": 0, "x": 0, "y": 9, "target": (3, 3)},  # Agent 1
    {"id": 1, "x": 9, "y": 9, "target": (6, 6)}   # Agent 2
]

def reset_agents():
    AGENTS[0]["x"], AGENTS[0]["y"] = 0, 9
    AGENTS[1]["x"], AGENTS[1]["y"] = 9, 9
    sio.emit("agents_update", AGENTS)

def move_agent(agent):
    tx, ty = agent["target"]
    if agent["x"] < tx:
        agent["x"] += 1
    elif agent["x"] > tx:
        agent["x"] -= 1
    if agent["y"] < ty:
        agent["y"] += 1
    elif agent["y"] > ty:
        agent["y"] -= 1
    return (agent["x"], agent["y"]) == (tx, ty)

@sio.event
def connect(sid, environ):
    sio.emit("agents_update", AGENTS)

@sio.on("start_formation")
def handle_start_formation(sid):
    # Move agents sequentially
    for agent in AGENTS:
        while True:
            reached_target = move_agent(agent)
            sio.emit("agents_update", AGENTS)
            if reached_target:
                break
            eventlet.sleep(0.5)  # Delay between steps

@sio.on("reset_formation")
def handle_reset_formation(sid):
    reset_agents()

if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)