#!/usr/bin/env python3
"""Sokoban level verifier: BFS over (player, boxes) states with corner
deadlock pruning. XSB format: # wall, space floor, $ box, . target,
* box-on-target, @ player, + player-on-target."""
from collections import deque

DIRS = {'U': (0, -1), 'D': (0, 1), 'L': (-1, 0), 'R': (1, 0)}


MAX_WIDTH, MAX_HEIGHT, MAX_BOXES = 38, 20, 10


def parse(level_text):
    rows = level_text.rstrip('\n').split('\n')
    if not 3 <= len(rows) <= MAX_HEIGHT:
        raise ValueError("height outside 3..20")
    width = len(rows[0])
    if not 3 <= width <= MAX_WIDTH or any(len(r) != width for r in rows):
        raise ValueError("width outside 3..38 or non-rectangular rows")
    walls, targets, boxes = set(), set(), set()
    players = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in '# .$*@+':
                raise ValueError(f"unknown symbol {ch!r}")
            if (x in (0, width-1) or y in (0, len(rows)-1)) and ch != '#':
                raise ValueError("open boundary")
            if ch == '#': walls.add((x,y))
            if ch in '.*+': targets.add((x,y))
            if ch in '$*': boxes.add((x,y))
            if ch in '@+': players.append((x,y))
    if len(players) != 1: raise ValueError("exactly one player required")
    if not 1 <= len(boxes) <= MAX_BOXES or len(boxes) != len(targets):
        raise ValueError("require 1..10 boxes and equal targets")
    # Every non-wall cell must connect when boxes are ignored.
    seen, q = {players[0]}, deque([players[0]])
    while q:
        x,y = q.popleft()
        for dx,dy in DIRS.values():
            p = (x+dx,y+dy)
            if 0 <= p[0] < width and 0 <= p[1] < len(rows) and p not in walls and p not in seen:
                seen.add(p); q.append(p)
    if len(seen) != width*len(rows)-len(walls):
        raise ValueError("disconnected floor")
    return walls, targets, boxes, players[0], width, len(rows)


def corner_deadlocks(walls, targets, width, height):
    dead = set()
    for x in range(width):
        for y in range(height):
            if (x, y) in walls or (x, y) in targets:
                continue
            up = (x, y - 1) in walls
            down = (x, y + 1) in walls
            left = (x - 1, y) in walls
            right = (x + 1, y) in walls
            if (up or down) and (left or right):
                dead.add((x, y))
    return dead


def solve_path(level_text, max_states=2_000_000):
    """FIFO BFS in player steps. First goal is a minimum in this metric only.
    None means unsolved OR resource limit; it never claims a push minimum.
    """
    walls, targets, boxes, player, width, height = parse(level_text)
    start = (player, frozenset(boxes))
    dead = corner_deadlocks(walls, targets, width, height)
    if boxes & dead: raise ValueError(f"box starts on dead square {boxes & dead}")
    parent = {start: None}
    q = deque([start])
    while q:
        state = q.popleft()
        ppos, bxs = state
        if bxs == targets:
            path = []
            while parent[state] is not None:
                state, d = parent[state]; path.append(d)
            return ''.join(reversed(path)), len(parent)
        for d,(dx,dy) in DIRS.items():
            np = (ppos[0]+dx,ppos[1]+dy)
            if not (0 <= np[0] < width and 0 <= np[1] < height) or np in walls: continue
            new_boxes = bxs
            if np in bxs:
                nb = (np[0]+dx,np[1]+dy)
                if not (0 <= nb[0] < width and 0 <= nb[1] < height) or nb in walls or nb in bxs or nb in dead: continue
                new_boxes = frozenset((bxs-{np})|{nb})
            nxt = (np,new_boxes)
            if nxt not in parent:
                if len(parent) >= max_states: return None,len(parent)
                parent[nxt] = (state,d); q.append(nxt)
    return None,len(parent)


def solve(level_text, max_states=2_000_000):
    path, states = solve_path(level_text, max_states)
    return (None if path is None else len(path)), states


def check(name, level_text, expect_solvable=True):
    try:
        dist, states = solve(level_text)
    except ValueError as e:
        print(f"[{name}] INVALID: {e}")
        return False
    if dist is None:
        print(f"[{name}] UNSOLVED (searched {states} states)")
        return False
    print(f"[{name}] solvable in {dist} moves (explored {states} states)")
    return True
