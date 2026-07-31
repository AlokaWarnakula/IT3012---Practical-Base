# agent.py
import random

# Movement deltas and turn tables shared by both agents.
DELTAS = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}
TURN_RIGHT = {'Up': 'Right', 'Right': 'Down', 'Down': 'Left', 'Left': 'Up'}


class SimpleReflexAgent:
    """Practical 2, Step 1.2 - Simple Reflex Agent.

    Pure Condition-Action (IF-THEN) rules. Reacts ONLY to the current percept
    and has NO memory (no __init__ state). Actions: 'Forward', 'Left', 'Right'.
    In a partially observable world this makes it loop forever in corners.
    """

    def sense_and_act(self, percept: dict) -> str:
        # RULE 1: IF food is on this tile -> move onto it / keep collecting.
        if percept.get('food_here'):
            return 'Forward'

        # RULE 2: IF a wall is ahead -> turn left.
        if percept.get('wall_ahead'):
            return 'Left'

        # RULE 3: ELSE -> move forward.
        return 'Forward'


class ModelBasedAgent:
    """Practical 2, Step 1.3 - Model-Based Reflex Agent.

    Keeps INTERNAL STATE (memory), so it can tell "been there" from "new":
      - Sensor Model:     learns a wall the instant it feels one ahead.
      - Transition Model: dead-reckons its own position after each move.
    It steers toward the least-visited, not-yet-tried neighbour, which lets it
    break the loops that trap the SimpleReflexAgent.
    """

    def __init__(self):
        self.pos = (0, 0)             # believed position (relative movement tracker)
        self.facing = 'Right'
        self.visited = {(0, 0): 1}    # how many times each cell was entered
        self.known_walls = set()      # cells learned to be walls
        self.tried = {}               # pos -> set of target directions already attempted

    def sense_and_act(self, percept: dict) -> str:
        facing = percept.get('facing', self.facing)
        self.facing = facing
        fdx, fdy = DELTAS[facing]
        front = (self.pos[0] + fdx, self.pos[1] + fdy)

        # SENSOR MODEL: remember the wall we can feel directly ahead.
        if percept.get('wall_ahead'):
            self.known_walls.add(front)

        # DECIDE a target direction: prefer not-yet-tried, then least-visited.
        tried = self.tried.setdefault(self.pos, set())
        candidates = []
        for d in ('Up', 'Right', 'Down', 'Left'):
            dx, dy = DELTAS[d]
            nb = (self.pos[0] + dx, self.pos[1] + dy)
            if nb not in self.known_walls:
                candidates.append(d)
        if candidates:
            target = min(candidates, key=lambda d: (d in tried,
                                                    self.visited.get((self.pos[0] + DELTAS[d][0],
                                                                      self.pos[1] + DELTAS[d][1]), 0)))
        else:
            target = facing
        tried.add(target)

        # ACT: if already facing the target, step forward; otherwise turn toward it.
        if target == facing:
            if not percept.get('wall_ahead'):
                self.pos = front                                  # TRANSITION MODEL: predict the move
                self.visited[self.pos] = self.visited.get(self.pos, 0) + 1
            return 'Forward'
        return 'Right' if TURN_RIGHT[facing] == target else 'Left'


class SearchAgent:
    """Practical 3 (next lab) - Problem-Solving Agent. Placeholder for now."""

    def bfs_search(self, start, goal, walls, grid_size):
        raise NotImplementedError("BFS is implemented in Practical 3.")
