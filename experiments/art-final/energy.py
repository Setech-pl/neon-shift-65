"""One Energy direction: recovered industrial vocabulary with readable objects.

Only pixels, offline selection and palette data. The forty robot states reuse
the existing ART4-A service chassis; their runtime sequencing is unchanged.
"""
import importlib.util
from pathlib import Path


def install(c, *, all_areas=False):
    if c.themes.AREA!=1 and not all_areas:return
    previous_wall,previous_kind,previous_scene=c.wall,c.decoration.wall_kind,c.scene
    c.themes.SPEC=dict(c.themes.SPEC,palette=[0xee,0x9c,0x02,0xe6,0])
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('art_final_robot',root/'experiments/art4-a/art.py')
    robot=importlib.util.module_from_spec(spec);spec.loader.exec_module(robot)
    frames=robot.Art('A').robot_frames()

    def wall_kind(mask,x,y,number):
        kind=previous_kind(mask,x,y,number)
        if mask in (5,10) and kind&15==1:
            return (1,5,6,7)[(x//3+y//2+number)%4]
        return kind

    def wall(mask,kind=0):
        variant=kind&15
        p=c.decode_tile(previous_wall(mask,kind if variant<5 else 0))
        # Recess the lower/right edge without changing the connected envelope.
        old=[row[:] for row in p]
        for y in range(16):
            for x in range(8):
                if old[y][x]==2 and (y==15 or old[y+1][x]==0 or x==7 or old[y][x+1]==0):p[y][x]=3
        if variant==5:
            if mask==10:
                for x in (1,5):
                    c.line(p,x,5,x,10,0);c.line(p,x+1,5,x+1,9,2)
                    p[5][x]=1
            elif mask==5:
                for y in (3,11):
                    c.line(p,2,y,5,y,0);c.line(p,2,y+1,4,y+1,1)
        elif variant==6:
            if mask==10:
                c.rect(p,2,6,4,4,0);c.line(p,2,6,5,6,2)
                p[8][3]=p[8][4]=1
            elif mask==5:
                c.rect(p,3,5,2,6,0);p[5][3]=1;p[10][4]=2
        elif variant==7:
            if mask==10:
                for x in (1,3,5):c.line(p,x,6,x+1,9,0)
                c.line(p,1,10,6,10,2)
            elif mask==5:
                for y in (4,7,10):c.line(p,3,y,4,y,0)
        return c.tile(p)

    def floors():
        tiles=[]
        for n in range(12):
            p=c.blank()
            if n:
                x,y=1+n%4,4+(n%3)*3
                c.line(p,x,y,x+1,y,3)
            tiles.append(c.tile(p))
        return tiles

    def floor_plan(rows,number,specs):
        goals=[(x,y) for y,row in enumerate(rows) for x,ch in enumerate(row) if ch in '.*+']
        return {(x,y):1+(x+3*y)%11 for y,row in enumerate(rows) for x,ch in enumerate(row)
                if ch==' ' and (x+2*y)%7==2 and all(abs(x-gx)+abs(y-gy)>2 for gx,gy in goals)},[]

    def container(docked=False,phase=None):
        p=c.blank();c.rect(p,1,2,6,11,1);c.rect(p,2,3,4,9,3)
        c.line(p,2,1,5,1,1);c.line(p,1,4,6,4,1)
        c.line(p,2,11,5,11,1);c.line(p,2,13,5,13,0)
        # Closed perimeter and cross-braced cargo: no head, limbs or wheels.
        c.rect(p,2,5,4,5,0)
        if not docked:
            c.line(p,2,5,5,9,1);c.line(p,5,5,2,9,1)
        if docked:
            for x,y in ((2,7),(3,8),(4,7),(5,6)):p[y][x]=2
        if phase is not None:p[2+phase*3][6]=2
        return p

    dock=c.blank()
    for y in (2,13):
        c.line(dock,1,y,2,y,2);c.line(dock,5,y,6,y,2)
    for x in (1,6):
        c.line(dock,x,3,x,5,2);c.line(dock,x,10,x,12,2)
    for x,y in ((3,6),(4,7),(3,8),(2,7)):dock[y][x]=1

    def scene(level,number,arrays):
        data=dict(arrays)
        data['gameplay_common']=c.tile(dock)+arrays['gameplay_common'][32:]
        data['robot_frames']=frames
        return previous_scene(level,number,data)

    c.wall,c.floors,c.container_pixels,c.scene=wall,floors,container,scene
    c.decoration.wall_kind,c.decoration.floor_plan=wall_kind,floor_plan
    c.decoration.VARIANT='ART-FINAL-Energy'
