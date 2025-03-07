import socketio
from flask import Flask
import eventlet

app = Flask(__name__)
sio = socketio.Server(cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app)

GRID_SIZE = 10
AGENT_COUNT = 20

TARGET_SHAPE = [(3,3), (4,3), (5,3), (6,3), (7,3),
 (3,4), (4,4), (5,4), (6,4), (7,4),
 (3,5), (4,5), (5,5), (6,5), (7,5),
 (3,6), (4,6), (5,6), (6,6), (7,6),
 ]
# [(4,2), (5,2),                    
#         (3,3),  (4,3), (5,3), (6,3), 
#     (2,4), (3,4),       (6,4), (7,4), 
#     (2,5), (3,5),       (6,5), (7,5),     
#         (3,6), (4,6), (5,6), (6,6),  
#                (4,7), (5,7)    
# ]

class Agent:
    def __init__(self, agent_id, start_pos, target):
        self.id = agent_id
        self.x, self.y = start_pos
        self.target = target
        self.path = []

def manhattan_distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def assign_targets(start_positions):
    targets = TARGET_SHAPE.copy()
    assignments = []
    for start in start_positions:
        closest = min(targets, key=lambda t: manhattan_distance(start, t))
        assignments.append((start, closest))
        targets.remove(closest)
    return assignments

def initialize_agents():
    start_positions = [(i%GRID_SIZE, GRID_SIZE-2+(i//GRID_SIZE)) 
                      for i in range(AGENT_COUNT)]
    assignments = assign_targets(start_positions)
    return [Agent(i, start, target) for i, (start, target) in enumerate(assignments)]

agents = initialize_agents()

def get_occupied_positions(current_agent_index):
    """Get positions occupied by other agents (both moved and unmoved)"""
    occupied = set()
    # Add final positions of already moved agents
    for agent in agents[:current_agent_index]:
        occupied.add((agent.x, agent.y))
    # Add initial positions of unmoved agents
    for agent in agents[current_agent_index+1:]:
        occupied.add((agent.x, agent.y))
    return occupied

def find_path(agent, current_agent_index):
    """A* inspired pathfinding with collision avoidance"""
    start = (agent.x, agent.y)
    target = agent.target
    open_set = [start]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, target)}
    occupied = get_occupied_positions(current_agent_index)

    while open_set:
        current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
        
        if current == target:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]  # Reverse path

        open_set.remove(current)
        
        # Generate all 8-direction neighbors
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue  # Skip current position
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Check grid boundaries
                if not (0 <= neighbor[0] < GRID_SIZE and 0 <= neighbor[1] < GRID_SIZE):
                    continue
                
                # Check occupancy
                if neighbor in occupied:
                    continue
                
                # Calculate tentative g-score
                tentative_g = g_score[current] + (1.414 if dx and dy else 1)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + manhattan_distance(neighbor, target)
                    if neighbor not in open_set:
                        open_set.append(neighbor)
    
    return []  # No path found

def reset_agents():
    global agents
    agents = initialize_agents()
    sio.emit("agents_update", [{"x": a.x, "y": a.y} for a in agents])

@sio.event
def connect(sid, environ):
    sio.emit("agents_update", [{"x": a.x, "y": a.y} for a in agents])

@sio.on("start_formation")
def handle_start_formation(sid):
    for index, agent in enumerate(agents):
        # Find path considering other agents' positions
        agent.path = find_path(agent, index)
        
        # Move along path
        for pos in agent.path:
            agent.x, agent.y = pos
            sio.emit("agents_update", [{"x": a.x, "y": a.y} for a in agents])
            eventlet.sleep(0.1)

@sio.on("reset_formation")
def handle_reset_formation(sid):
    reset_agents()

if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)