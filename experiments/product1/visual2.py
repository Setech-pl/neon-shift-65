"""VISUAL2 Energy: pixels and offline selection in the existing strip compiler.

No target code, buffers, alternate renderer, geometry or device timing here.
Pixel1=PF0 warm light, pixel2=PF1 cool edge, pixel3=PF2 dark steel.
Object inverse pixel3=PF3 brass. Background ink retains VIS1's dim PF3.
"""
from collections import deque
import json


def install(c, art=None):
    assert c.themes.AREA == 1
    c.themes.SPEC = dict(c.themes.SPEC, palette=[0xee, 0x9a, 0x94, 0xe6, 0])
    previous_scene, previous_device = c.scene, c.device
    context, plan = {}, {}

    def wall(mask, kind=0):
        p = c.blank()

        def metal(x, y):
            if 0 <= x < 8 and 0 <= y < 16:
                return (2 <= x <= 5 and 4 <= y <= 11 or
                        mask & 1 and 2 <= x <= 5 and y < 6 or
                        mask & 4 and 2 <= x <= 5 and y >= 10 or
                        mask & 2 and x >= 4 and 4 <= y <= 11 or
                        mask & 8 and x < 4 and 4 <= y <= 11)
            return (x < 0 and mask & 8 and 4 <= y <= 11 or
                    x >= 8 and mask & 2 and 4 <= y <= 11 or
                    y < 0 and mask & 1 and 2 <= x <= 5 or
                    y >= 16 and mask & 4 and 2 <= x <= 5)

        for y in range(16):
            for x in range(8):
                if not metal(x, y):
                    continue
                p[y][x] = 3
                if not metal(x+1, y) or not metal(x, y+1):
                    p[y][x] = 0
                elif not metal(x, y-1) or not metal(x-1, y):
                    p[y][x] = 2
        variant = kind & 15
        if mask == 10:
            if variant == 1:
                c.line(p, 5, 6, 5, 9, 0)
                p[6][2] = 2
            elif variant == 2:
                c.rect(p, 2, 6, 4, 3, 0)
                c.line(p, 2, 9, 5, 9, 3)
                p[7][3] = 1
            elif variant == 3:
                start, end = (1 if kind & 16 else 0), (6 if kind & 32 else 7)
                c.rect(p, start, 6, end-start+1, 4, 0)
                c.line(p, start, 7, end, 7, 2)
                c.line(p, start, 8, end, 8, 3)
                for x in ([start] if kind & 16 else []) + ([end] if kind & 32 else []):
                    c.line(p, x, 6, x, 9, 3)
                    p[6][x] = 2
            elif variant == 4:
                for x in (2, 4, 6):
                    c.line(p, x, 6, x, 8, 0)
        elif mask == 5:
            if variant == 1:
                c.line(p, 3, 8, 4, 8, 0)
            elif variant == 2:
                c.rect(p, 3, 5, 1, 6, 0)
                p[6][3] = 1
            elif variant == 3:
                c.line(p, 3, 0, 3, 15, 0)
                c.line(p, 4, 0, 4, 15, 3)
                for y in ([1] if kind & 16 else []) + ([14] if kind & 32 else []):
                    c.line(p, 2, y, 4, y, 2)
            elif variant == 4:
                for y in (5, 8, 11):
                    c.line(p, 3, y, 4, y, 0)
        elif variant:
            p[7][3] = 0
        return c.tile(p)

    def floors():
        result = []
        for n in range(12):
            p = c.blank()
            c.line(p, 6, 15, 7, 15, 3)
            p[14][7] = 3
            if n:
                # Three small plate marks at most per scene; never an object.
                x, y = 1+(n % 3), 5+(n % 4)
                c.line(p, x, y, x+2, y, 3)
                c.line(p, 1, 15, 5, 15, 3)
            result.append(c.tile(p))
        return result

    def floor_plan(rows, number, specs):
        result = {}
        docks = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value in '.*+']
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                if value in ' $@' and (x+2*y) % 5 == 0 and all(abs(x-a)+abs(y-b)>1 for a, b in docks):
                    if len(result) < 3:
                        result[x, y] = 1+(x+3*y) % 11
        return result, []

    def container(docked=False, phase=None):
        p = c.blank()
        c.rect(p, 1, 2, 6, 11, 3)
        c.line(p, 2, 1, 5, 1, 1)
        c.line(p, 1, 2, 5, 2, 1)
        c.line(p, 1, 3, 1, 11, 1)
        c.line(p, 6, 3, 6, 12, 0)
        c.line(p, 2, 13, 5, 13, 0)
        c.line(p, 2, 10, 5, 10, 0)
        c.rect(p, 3, 5, 2, 4, 0)
        c.line(p, 3, 5, 4, 5, 1)
        p[7][3] = 1
        if docked:
            for x, y in ((2, 7), (3, 8), (4, 7), (5, 6)):
                p[y][x] = 2
        if phase is not None:
            p[2+phase*3][1] = 2
        return p

    dock = c.blank()
    for y in (3, 12):
        c.line(dock, 1, y, 6, y, 2)
    for x in (1, 6):
        c.line(dock, x, 4, x, 6, 2)
        c.line(dock, x, 9, x, 11, 2)
    dock[7][3] = dock[7][4] = 1

    def device(kind, phase):
        old = previous_device(kind, phase)
        h, w = len(old), len(old[0])
        p = [[0 if v == 3 else 3 if v == 2 else 2 if v == 1 else 0 for v in row] for row in old]
        for y in range(3, h-3):
            for x in range(3, w-3):
                if old[y][x] == 1:
                    p[y][x] = 1
                elif old[y][x] == 2 and (kind == 'fan' or kind == 'terminal' and y < 19):
                    p[y][x] = 2
        # A fixed right-hand mounting socket, shared by all existing phases.
        c.line(p, w-3, h//2, w-1, h//2, 3)
        return p

    def split(p):
        # Unlike old cool(), preserve dark PF2 steel in environmental devices.
        return {(x//8, y//16): c.tile([row[x:x+8] for row in p[y:y+16]])
                for y in range(0, len(p), 16) for x in range(0, len(p[0]), 8)}

    def scene(level, number, arrays):
        w, h = level.get('visual_size', (len(level['rows'][0]), len(level['rows'])))
        rows = level['rows']
        specs = c.decoration.devices([('terminal',1,0,17,0), ('cabinet',14,1,31,7),
                  ('fan',4,6,6,0), ('fan',11,6,9,3), ('gate',10,0,19,0),
                  ('installation',6,0,11,4)], number, level)
        # Section ownership uses the authored perimeter, including real walls
        # that cannot be reached by the player. Never uses reachability.
        masks = {(x, y): sum(bit for dx, dy, bit in ((0,-1,1),(1,0,2),(0,1,4),(-1,0,8))
                 if 0 <= x+dx < w and 0 <= y+dy < h and rows[y+dy][x+dx] == '#')
                 for y in range(h) for x in range(w) if rows[y][x] == '#'}
        plan.clear()
        for mask in (10, 5):
            dx, dy = (1, 0) if mask == 10 else (0, 1)
            eligible = {pos for pos, value in masks.items() if value == mask}
            for run, (x, y) in enumerate(sorted(pos for pos in eligible if (pos[0]-dx,pos[1]-dy) not in eligible)):
                cells = []
                while (x, y) in eligible:
                    cells.append((x, y)); x += dx; y += dy
                start, section = 0, run+(1 if mask == 10 else 2)
                while start < len(cells):
                    kind = (0, 3, 1, 0, 2, 0, 4)[section % 7]
                    count = 1 if kind == 2 else 2 if kind in (1,3,4) else 3
                    group = cells[start:start+count]
                    for i, pos in enumerate(group):
                        plan[pos] = kind | ((16 if i == 0 else 0) | (32 if i == len(group)-1 else 0) if kind == 3 else 0)
                    start += count
                    section += 1
        # Lay three mounting leads in the existing background glyph layer.
        # Pixel routes avoid the full authored board and every device rectangle.
        bx, by = 16, 24
        blocked = {(x, y) for y in range(by, by+h*16) for x in range(bx, bx+w*8)}
        rects = []
        for kind, x, y, period, phase in specs:
            p = device(kind, 0)
            xx, yy, ww, hh = bx+x*8, by+y*16, len(p[0]), len(p)
            rects.append((kind, xx, yy, ww, hh))
            blocked.update((a, b) for b in range(yy, yy+hh) for a in range(xx, xx+ww))
        pipes, routes = set(), []
        for kind, x, y, ww, hh in sorted(rects, key=lambda r: -r[1]):
            if len(routes) == 3:
                break
            start = (x+ww, y+hh//2)
            if start in blocked or not (0 <= start[0] < 159 and 2 <= start[1] < 174):
                continue
            q, parents = deque([start]), {start: None}
            end = None
            while q:
                point = q.popleft()
                if point[0] == 157:
                    end = point; break
                for dx, dy in ((1,0),(0,1),(0,-1),(-1,0)):
                    nxt = point[0]+dx, point[1]+dy
                    if 1 <= nxt[0] <= 157 and 2 <= nxt[1] <= 173 and nxt not in blocked and nxt not in parents:
                        parents[nxt] = point; q.append(nxt)
            if end is not None:
                route = []
                while end is not None:
                    route.append(end); pipes.add(end); end = parents[end]
                routes.append(dict(kind=kind, points=route))
        if routes:
            lo = min(route['points'][0][1] for route in routes)
            hi = max(route['points'][0][1] for route in routes)
            pipes.update((157, y) for y in range(lo, hi+1) if (157, y) not in blocked)
        context['pipes'] = pipes
        data = dict(arrays)
        data['gameplay_common'] = c.tile(dock)+arrays['gameplay_common'][32:]
        if art is not None:
            data['robot_frames'] = art.robot_frames()
        result = previous_scene(level, number, data)
        (c.OUT/f'scene-{number}-visual2.json').write_text(json.dumps(dict(
            palette=c.themes.SPEC['palette'], visual_size=[w,h], routes=routes,
            section_cells=[dict(x=x,y=y,kind=kind) for (x,y),kind in sorted(plan.items())],
            no_route_on_board=all(point not in blocked for point in pipes)), indent=2)+'\n')
        return result

    def background(pos, original, animated):
        if pos in animated:
            return original
        row, col = divmod(pos, 40)
        # Quiet service rails replace the old unconnected hatching. Existing
        # animated edge indicators keep their exact absolute positions.
        p = bytearray(8)
        for yy in range(8):
            for xx in range(4):
                if (col*4+xx, (row-2)*8+yy) in context.get('pipes', set()):
                    p[yy] |= 1 << (6-2*xx)
        return bytes(p)

    if art is not None:
        wall, floors, container, device, dock, floor_plan = art.resources(c)
        c.themes.SPEC = dict(c.themes.SPEC, palette=art.PALETTE)
        # Reuse the existing route plan; dim metal ink on the same glyph layer.
        previous_intern = c.Strip.intern
        def intern(self, data, who, selector=0):
            if who.startswith('background'):
                data = bytes(sum((3 if (v >> k) & 3 else 0) << k
                                 for k in (0,2,4,6)) for v in data)
                who = 'art4-' + who
                selector = 0
            return previous_intern(self, data, who, selector)
        c.Strip.intern = intern
    c.wall, c.floors, c.container_pixels, c.device, c.split = wall, floors, container, device, split
    c.scene, c.decoration.background, c.decoration.floor_plan = scene, background, floor_plan
    c.decoration.wall_kind = lambda mask, x, y, number: plan.get((x,y), 0)
    c.decoration.VARIANT = 'VISUAL2-energy-service-bay' if art is None else 'ART4-A-'+art.direction
