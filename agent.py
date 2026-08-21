# agent.py
import random
import math                     # Lab 4: straight-line distance for the Euclidean heuristic
from collections import deque   # Lab 3: FIFO frontier for BFS
import heapq                    # Lab 3/4: priority-queue frontier for UCS and A*

# Movement deltas and turn tables shared by both agents.
DELTAS = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}
TURN_RIGHT = {'Up': 'Right', 'Right': 'Down', 'Down': 'Left', 'Left': 'Up'}
TURN_LEFT = {'Up': 'Left', 'Left': 'Down', 'Down': 'Right', 'Right': 'Up'}


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
    """Practical 3 - Goal-Based / Problem-Solving (Planning) Agent.

    Unlike the reflex agents, this agent is given the WORLD MODEL in its percept
    ('grid_size', 'walls', 'all_food') and uses UNINFORMED SEARCH to compute a
    complete plan (a sequence of moves) OFFLINE before acting. It then executes
    that plan one step at a time.

    The three searches share one node-expansion loop; only the FRONTIER data
    structure changes:
        BFS -> FIFO queue      (deque.popleft)  -> shallowest node first
        DFS -> LIFO stack      (list.pop)        -> deepest node first
        UCS -> priority queue  (heapq.heappop)   -> lowest path cost g(n) first
    A `reached` set makes every search a GRAPH search (no re-expanding a state),
    which is what stops DFS from looping forever.
    """

    def __init__(self):
        # Step 1.3: planning state.
        self.plan = []                 # queued game actions ('Forward'/'Left'/'Right')
        self.active_algo = 'BFS'       # switch to 'DFS' / 'UCS' / 'AStar' to compare paths
        # The percept never reveals the true position, so — like the model-based
        # agent — we dead-reckon our own location, starting at the spawn tile.
        self.pos = (0, 0)
        self.facing = 'Right'

    # ---- Shared helpers -------------------------------------------------
    @staticmethod
    def _neighbors(node, walls, grid_size):
        """Yield (direction, next_cell) for the 4 legal moves from `node`."""
        w, h = grid_size
        for d, (dx, dy) in DELTAS.items():
            nxt = (node[0] + dx, node[1] + dy)
            if 0 <= nxt[0] < w and 0 <= nxt[1] < h and nxt not in walls:
                yield d, nxt

    @staticmethod
    def _reconstruct(parent, start, goal):
        """Walk parent pointers back from goal to start -> list of directions."""
        directions = []
        node = goal
        while node != start:
            prev, d = parent[node]
            directions.append(d)
            node = prev
        directions.reverse()
        return directions

    # ---- Step 1.1: heuristics for informed search ------------------------
    def manhattan_distance(self, pos, goal):
        """h(n) = |x1-x2| + |y1-y2|. Admissible for 4-way (no diagonal) movement."""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        """h(n) = sqrt((x1-x2)^2 + (y1-y2)^2). Straight-line distance."""
        return math.sqrt((pos[0] - goal[0]) ** 2 + (pos[1] - goal[1]) ** 2)

    # ---- Step 1.2: the three uninformed searches ------------------------
    def bfs_search(self, start, goal, walls, grid_size):
        """Breadth-First Search. FIFO frontier -> optimal on unit-cost grid."""
        frontier = deque([start])          # FIFO queue
        reached = {start}                  # graph-search: visited states
        parent = {}                        # child -> (parent, direction taken)
        while frontier:
            node = frontier.popleft()      # <-- shallowest first
            if node == goal:
                return self._reconstruct(parent, start, goal)
            for d, nxt in self._neighbors(node, walls, grid_size):
                if nxt not in reached:
                    reached.add(nxt)
                    parent[nxt] = (node, d)
                    frontier.append(nxt)
        return []                          # no path

    def dfs_search(self, start, goal, walls, grid_size):
        """Depth-First Search. LIFO frontier -> deep, winding, NOT optimal."""
        frontier = [start]                 # LIFO stack
        reached = {start}
        parent = {}
        while frontier:
            node = frontier.pop()          # <-- deepest first
            if node == goal:
                return self._reconstruct(parent, start, goal)
            for d, nxt in self._neighbors(node, walls, grid_size):
                if nxt not in reached:
                    reached.add(nxt)
                    parent[nxt] = (node, d)
                    frontier.append(nxt)
        return []

    def ucs_search(self, start, goal, walls, grid_size):
        """Uniform-Cost Search. Priority queue ordered by g(n) (path cost)."""
        counter = 0                        # tie-breaker so heapq never compares tuples
        frontier = [(0, counter, start)]   # (cost, seq, node)
        best_cost = {start: 0}
        parent = {}
        while frontier:
            cost, _, node = heapq.heappop(frontier)   # <-- lowest g(n) first
            if node == goal:
                return self._reconstruct(parent, start, goal)
            if cost > best_cost.get(node, float('inf')):
                continue                   # stale, cheaper path already expanded
            for d, nxt in self._neighbors(node, walls, grid_size):
                new_cost = cost + 1        # every step costs 1 in this grid
                if new_cost < best_cost.get(nxt, float('inf')):
                    best_cost[nxt] = new_cost
                    parent[nxt] = (node, d)
                    counter += 1
                    heapq.heappush(frontier, (new_cost, counter, nxt))
        return []

    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan'):
        """A* Search. Priority queue ordered by f(n) = g(n) + h(n).

        Like UCS, but each node also carries a heuristic estimate of the
        remaining distance to the goal, so the search is drawn toward the
        goal instead of expanding outward evenly in every direction.
        """
        heuristic = self.manhattan_distance if heuristic_type == 'manhattan' else self.euclidean_distance
        h_start = heuristic(start_pos, goal_pos)
        frontier = [(h_start, 0, start_pos, [])]   # (f_cost, g_cost, current_pos, path_taken)
        reached_states = set()

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)  # <-- lowest f(n) first
            if current_pos == goal_pos:
                return path_taken
            if current_pos in reached_states:
                continue                   # stale entry, already expanded via a cheaper route
            reached_states.add(current_pos)

            for d, nxt in self._neighbors(current_pos, walls, grid_size):
                if nxt not in reached_states:
                    g_new = g_cost + 1
                    h_new = heuristic(nxt, goal_pos)
                    f_new = g_new + h_newt
                    heapq.heappush(frontier, (f_new, g_new, nxt, path_taken + [d]))
        return []                          # no path

    # ---- Step 1.3: plan once, then execute step-by-step -----------------
    def _directions_to_actions(self, directions):
        """Turn a cardinal path (['Up','Right',...]) into this turn-based
        environment's actions, inserting rotations before each 'Forward'."""
        actions = []
        facing = self.facing
        for target in directions:
            while facing != target:        # rotate toward the target heading
                if TURN_RIGHT[facing] == target:
                    actions.append('Right'); facing = TURN_RIGHT[facing]
                elif TURN_LEFT[facing] == target:
                    actions.append('Left'); facing = TURN_LEFT[facing]
                else:                       # 180 deg turn
                    actions.append('Right'); facing = TURN_RIGHT[facing]
            actions.append('Forward')
        return actions

    def sense_and_act(self, percept: dict) -> str:
        self.facing = percept.get('facing', self.facing)  # resync heading with env

        # 1) If we have no plan, form one with the selected search algorithm.
        if not self.plan:
            foods = [tuple(f) for f in percept.get('all_food', [])]
            if not foods:
                return 'Left'                              # nothing left: idle turn
            # Pick the closest pellet by Manhattan distance.
            goal = min(foods, key=lambda f: abs(f[0] - self.pos[0]) + abs(f[1] - self.pos[1]))
            walls = set(map(tuple, percept.get('walls', [])))
            grid_size = percept.get('grid_size', (0, 0))
            search = {'BFS': self.bfs_search,
                      'DFS': self.dfs_search,
                      'UCS': self.ucs_search,
                      'AStar': self.astar_search}[self.active_algo]
            directions = search(self.pos, goal, walls, grid_size)
            self.plan = self._directions_to_actions(directions)
            # Executing the whole plan lands us on the pellet: dead-reckon there.
            self.pos = goal

        if not self.plan:                                  # goal unreachable
            return 'Left'

        # 2) Execute the plan one action at a time.
        return self.plan.pop(0)
