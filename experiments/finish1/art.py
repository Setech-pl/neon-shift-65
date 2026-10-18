"""FINISH1: common industrial material and objects, four equipment identities.

Offline pixels only. All coordinates, animation periods and live buffers remain
owned by the existing compiler/engine. Palette order is PF0, PF1, PF2, PF3, BK.
"""
import importlib.util
from pathlib import Path

PALETTES = {
    1: [0xee, 0x9a, 0x02, 0x06, 0],
    2: [0xee, 0xba, 0x02, 0x06, 0],
    3: [0xee, 0x8a, 0x02, 0x06, 0],
    4: [0xee, 0x3a, 0x02, 0x06, 0],
}


def install(c):
    area=c.themes.AREA
    c.themes.SPEC=dict(c.themes.SPEC,palette=PALETTES[area])
    root=Path(__file__).resolve().parents[2]
    # Reuse the closed cargo/dock and forty service-robot frames from f5df646.
    # The common wall below replaces its Energy wall; the area's own devices
    # remain intact. The optional argument leaves historical callers unchanged.
    if area!=1:
        spec=importlib.util.spec_from_file_location('finish1_objects',root/'experiments/art-final/energy.py')
        objects=importlib.util.module_from_spec(spec);spec.loader.exec_module(objects)
        objects.install(c,all_areas=True)
        c.themes.SPEC=dict(c.themes.SPEC,palette=PALETTES[area])

    def wall(mask,kind=0):
        p=c.blank()
        c.rect(p,2,4,4,8,2)
        for bit,x,y,w,h in ((1,2,0,4,6),(2,4,4,4,8),(4,2,10,4,6),(8,0,4,4,8)):
            if mask&bit:c.rect(p,x,y,w,h,2)
        # A consistent two-sided bevel: connected arms remain connected.
        solid=[[v!=0 for v in row] for row in p]
        for y in range(16):
            for x in range(8):
                if not solid[y][x]:continue
                if y==15 or not solid[y+1][x] or x==7 or not solid[y][x+1]:p[y][x]=3
        if mask==10:
            c.line(p,0,5,7,5,2);c.line(p,0,10,7,10,3)
            if kind==0:  # Riveted metal plate.
                c.line(p,3,6,3,9,0);p[6][2]=1
            elif kind==1:  # Recessed access lid.
                c.rect(p,2,6,4,4,0);c.line(p,2,6,5,6,2);p[8][4]=1
            elif kind==2:  # Narrow ventilation slots.
                for x in (1,3,5):c.line(p,x,7,x,9,0)
            else:  # Domain-specific service trunk, same metal envelope.
                c.rect(p,0,7,8,3,0);c.line(p,0,8,7,8,2)
                if area==2:c.line(p,0,10,7,10,2)
                elif area==3:
                    for x in (1,5):p[7][x]=1
                elif area==4:
                    for x in (1,4):c.line(p,x,7,x+1,9,3)
        elif mask==5:
            c.line(p,2,0,2,15,2);c.line(p,5,0,5,15,3)
            if kind==0:c.line(p,3,7,4,7,0);p[6][3]=1
            elif kind==1:
                c.rect(p,3,4,2,8,0);p[5][3]=2;p[10][4]=1
            elif kind==2:
                for y in (3,7,11):c.line(p,3,y,4,y,0)
            else:
                c.line(p,3,0,3,15,0)
                if area==2:c.line(p,4,0,4,15,2)
                elif area==3:
                    for y in (3,11):p[y][3]=1
                elif area==4:
                    for y in (4,10):p[y][4]=0
        else:
            c.line(p,3,6,4,6,2);c.line(p,3,9,4,9,0)
        return c.tile(p)

    c.wall=wall
    c.decoration.wall_kind=lambda mask,x,y,number: (x//3+y//2)%4
    if area!=1:
        # Recovered scene-map vocabulary replaces sparse ART3 stubs. Keep it
        # below gameplay contrast through the existing per-glyph PF3 selector.
        c.decoration.background=lambda pos,original,animated:original
        original_intern=c.Strip.intern
        def intern(self,data,who,selector=0):
            if who.startswith('background'):
                data=bytes(sum((3 if (v>>k)&3 else 0)<<k for k in (0,2,4,6)) for v in data)
                selector=128
            return original_intern(self,data,who,selector)
        c.Strip.intern=intern
    c.decoration.VARIANT='FINISH1-four-area-industrial'
