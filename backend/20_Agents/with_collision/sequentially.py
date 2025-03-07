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
# [              (4,2), (5,2)                    
#         (3,3), (4,3), (5,3), (6,3), 
#     (2,4), (2,4),       (6,4), (7,4), 
#     (2,5), (2,5),       (6,5), (7,5),     
#         (3,6), (4,6), (5,6), (6,6),  
#                (4,7), (5,7)    
# ]

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

def move_agent(agent):
    tx, ty = agent["target"]
    # X movement
    if agent["x"] < tx:
        agent["x"] += 1
    elif agent["x"] > tx:
        agent["x"] -= 1
    # Y movement
    if agent["y"] < ty:
        agent["y"] += 1
    elif agent["y"] > ty:
        agent["y"] -= 1
    return (agent["x"], agent["y"]) == (tx, ty)

@sio.event
def connect(sid, environ):
    sio.emit("agents_update", agents)

@sio.on("start_formation")
def handle_start_formation(sid):
    for agent in agents:
        while True:
            reached_target = move_agent(agent)
            sio.emit("agents_update", agents)
            if reached_target:
                break
            eventlet.sleep(0.3)  # Adjust speed here (0.3s per step)

@sio.on("reset_formation")
def handle_reset_formation(sid):
    reset_agents()

if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)