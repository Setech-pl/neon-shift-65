"""VIS1-r2: functional wall sections in the existing offline Energy overlay.

kind=0 retains VIS1's quiet segment (also the maximum fixture's indicator base).
All detail stays in the existing connected metal envelope and fixed font banks.
No runtime decoration, new animation, or alternate renderer is introduced.
"""
import json
import vis1_base


def install(c):
    vis1_base.install(c)
    if c.themes.AREA != 1:
        return
    previous_wall = c.wall
    previous_devices = c.decoration.devices
    plan = {}

    def devices(old, number, level):
        specs = previous_devices(old, number, level)
        rows = level['rows']
        w, h = len(rows[0]), len(rows)
        masks = {}
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                if value == '#':
                    masks[x, y] = sum(bit for dx, dy, bit in
                        ((0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8))
                        if 0 <= x+dx < w and 0 <= y+dy < h
                        and rows[y+dy][x+dx] == '#')
        # Exclude the unchanged authored devices and maximum's stress lamps.
        occupied = set()
        for kind,x,y,period,phase in specs:
            occupied.update((x+dx,y+dy) for dx,dy in c.split(c.device(kind,0)))
        if number == 1:
            occupied.update((x,0) for x in range(2,14))
        plan.clear()
        # Corners/junctions keep a solid elbow and a small plate joint.
        plan.update({pos:1 for pos,m in masks.items()
                     if m not in (5,10) and pos not in occupied})
        sections = []
        sequence = (1, 3, 0, 4, 1, 2, 0)
        for mask in (10, 5):
            dx, dy = (1,0) if mask == 10 else (0,1)
            eligible = {pos for pos,m in masks.items() if m == mask and pos not in occupied}
            starts = sorted((x,y) for x,y in eligible if (x-dx,y-dy) not in eligible)
            for run_index, (x,y) in enumerate(starts):
                run = []
                while (x,y) in eligible:
                    run.append((x,y)); x += dx; y += dy
                index = 0
                section = (run_index + number + (0 if mask == 10 else 1)) % len(sequence)
                while index < len(run):
                    kind = sequence[section % len(sequence)]
                    count = min(1 if kind == 2 else 2 if kind in (0,4) else 3,
                                len(run)-index)
                    cells = run[index:index+count]
                    for n,pos in enumerate(cells):
                        # Conduit end collars close inside metal; neighbouring
                        # conduit cells share continuous centreline sockets.
                        plan[pos] = kind | ((16 if n == 0 else 0) |
                                          (32 if n == count-1 else 0) if kind == 3 else 0)
                    sections.append(dict(mask=mask,kind=kind,cells=cells))
                    index += count; section += 1
        (c.OUT/f'scene-{number}-wall-sections.json').write_text(json.dumps(dict(
            kinds={0:'quiet VIS1',1:'seamed riveted plate',2:'recessed service panel',
                   3:'conduit with end collars',4:'vent shield'},
            sections=sections, cells=[dict(x=x,y=y,mask=masks[x,y],kind=k)
                for (x,y),k in sorted(plan.items())]),indent=2)+'\n')
        return specs

    def wall(mask, kind=0):
        base = previous_wall(mask, 0)
        if not kind:
            return base
        p = c.decode_tile(base)
        variant = kind & 15
        # Preserve the same envelope, material and upper-left lighting.
        # Narrow vertical walls have only four logical pixels across.
        if mask == 10:
            if variant == 1:
                c.line(p,3,5,3,10,0)
                p[6][2] = p[9][4] = 1
            elif variant == 2:
                c.rect(p,2,6,4,4,0)
                c.line(p,3,7,4,7,2); p[9][5] = 1
            elif variant == 3:
                start, end = (1 if kind & 16 else 0), (6 if kind & 32 else 7)
                c.rect(p,start,7,end-start+1,3,0)
                c.line(p,start,8,end,8,2)
                for x in ([start] if kind & 16 else []) + ([end] if kind & 32 else []):
                    c.line(p,x,7,x,9,2); p[7][x] = 1
            elif variant == 4:
                for x in (2,4,6):
                    c.line(p,x,6,x,9,0)
                c.line(p,1,10,6,10,2)
        elif mask == 5:
            if variant == 1:
                c.line(p,3,7,4,7,0)
                p[6][2] = p[9][5] = 1
            elif variant == 2:
                c.rect(p,3,4,2,8,0)
                p[5][3] = p[10][3] = 2; p[11][4] = 1
            elif variant == 3:
                start, end = (2 if kind & 16 else 0), (13 if kind & 32 else 15)
                c.rect(p,3,start,2,end-start+1,0)
                c.line(p,3,start,3,end,2)
                for y in ([start] if kind & 16 else []) + ([end] if kind & 32 else []):
                    c.line(p,3,y,4,y,1)
            elif variant == 4:
                for y in (4,7,10):
                    c.line(p,3,y,4,y,0)
        else:
            # Ends, elbows and T joints use a common inset seam, never a
            # conduit cut through an absent arm or an opening into floor.
            c.line(p,3,7,4,7,0)
            p[6][2] = 1
            p[10][5] = 0
        return c.tile(p)

    c.wall = wall
    c.decoration.devices = devices
    c.decoration.wall_kind = lambda mask,x,y,number: plan.get((x,y),0)
    c.decoration.VARIANT = 'VIS1-r2-energy-wall-sections'
