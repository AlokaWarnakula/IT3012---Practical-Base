# IT3012 – Practical 03: Uninformed Search — Answers

## Part 1 — Implementation summary

- **Step 1.1 (`visual_grid_game.py` → `get_percept`)**: added `'grid_size'`, `'walls'`,
  and `'all_food'` so the agent receives an abstract model of the world it can
  simulate offline.
- **Step 1.2 (`agent.py` → `SearchAgent`)**: one shared node-expansion loop with a
  swappable frontier — `bfs_search` (FIFO `deque.popleft`), `dfs_search`
  (LIFO `list.pop`), `ucs_search` (priority queue `heapq.heappop`, ordered by path
  cost *g(n)*). All three keep a `reached` set → **graph search**.
- **Step 1.3**: `__init__` holds `self.plan = []` and `self.active_algo = 'BFS'`.
  `sense_and_act` plans to the closest pellet when the plan is empty, then returns
  one action per tick via `self.plan.pop(0)`.

**Observed result** (10×10, 6 pellets, same seed): BFS = 37 steps, UCS = 37 steps
(direct/optimal), DFS = 79 steps (winding). On an open `(0,0)→(3,2)` map BFS/UCS
return the optimal 5-move path; DFS returns a 17-move detour.

---

## Part 2 — Theoretical Evaluation

### 1. (Remember) Difference between the *State Space* and the *Search Tree*

The **state space** is the *problem*: the complete set of distinct configurations
of the world (every reachable grid cell) plus the legal transitions between them.
It is a fixed **graph** — each cell exists exactly once, no matter how many ways
you can reach it.

The **search tree** is the *process*: the structure the algorithm builds while
exploring that graph from a chosen start node. Its nodes are **paths**, not states,
so the *same* state can appear many times in the tree (reached along different
routes). The state space is finite here (≤ width×height cells); the search tree can
be far larger, even infinite, if repeated states are not pruned.

### 2. (Understand) What the `reached` set solves, and DFS without it

The `reached` (visited) set converts a **tree search into a graph search**: it
records every state already generated so a state is never expanded twice. This
solves the problem of **redundant paths / revisiting states**, and in particular
prevents getting caught in **cycles/loops** in the grid graph.

Without it, DFS would keep re-expanding the same cells — e.g. step Right then Left
then Right forever between two adjacent tiles — and **loop infinitely**, never
terminating (or overflowing the frontier/recursion), because in a grid every cell
has neighbours that lead back to already-visited cells.

### 3. (Analyze) Why BFS is optimal here but DFS is winding/suboptimal

Every move in this grid has the **same unit cost (1)**. BFS expands nodes strictly
in order of increasing **depth** (path length), so the first time it reaches the
goal it has done so via a path of minimum length — and with equal step costs,
minimum length = minimum cost = **optimal**. Its FIFO frontier guarantees all
depth-*d* nodes are exhausted before any depth-*(d+1)* node.

DFS instead dives as deep as possible along one branch (LIFO frontier) before
backtracking. It returns the **first** path it stumbles onto, not the shortest, so
it produces long, **winding** routes. DFS is neither complete on infinite spaces
(fixed here only by the `reached` set) nor optimal — depth of discovery, not cost,
drives it.

### 4. (Evaluate) On a 1000×1000 grid — memory bottleneck of BFS vs DFS

Let *b* = branching factor (≈4 here) and *d/m* = solution depth / max depth.

- **BFS** stores the **entire frontier**, i.e. every node at the current depth:
  time **O(b^d)** and, critically, space **O(b^d)**. It must hold an exponentially
  wide layer (bounded here by the number of grid cells, ~10^6) in memory at once —
  so on a 1000×1000 grid it can exhaust RAM *before* reaching food. **UCS** has the
  same weakness (space O(b^(1+⌊C*/ε⌋))), storing a large frontier ordered by cost.
- **DFS** stores only the nodes along the **current path plus their unexpanded
  siblings**: space **O(b·m)** — *linear*, not exponential. That is DFS's one real
  advantage: it is dramatically more **memory-efficient**. (With the `reached` set,
  memory grows toward O(states), but the raw frontier stays linear.)

**Contrast:** BFS/UCS trade memory for optimality — they find the shortest path but
the frontier blows up exponentially with depth. DFS trades optimality for memory —
it barely uses space but may return a poor path (or wander deep). On a massive grid,
BFS/UCS hit a **space bottleneck**, while DFS stays memory-cheap at the cost of path
quality.
