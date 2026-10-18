"""Two authored Energy pixel vocabularies in the existing strip compiler.

8x16 logical tiles; lighting comes from upper left. No target routines.
The different constructions remain distinct without their palette differences.
"""
from assets import encode_tile


class Art:
    def __init__(self, direction):
        assert direction in ('A', 'B')
        self.direction = direction
        self.PALETTE = ([0xee,0x08,0x04,0xe6,0] if direction=='A'
                        else [0x0e,0x98,0x94,0xe6,0])

    def resources(self, c):
        self.c = c
        return self.wall, self.floors, self.container, self.device, self.dock(), self.floor_plan

    def wall(self, mask, kind=0):
        c = self.c
        p = c.blank()
        a = self.direction == 'A'
        left, right, top, bottom = (1,6,2,13) if a else (2,5,3,12)
        def metal(x,y):
            return (left<=x<=right and top<=y<=bottom or
                    mask&1 and left<=x<=right and y<=bottom or
                    mask&4 and left<=x<=right and y>=top or
                    mask&8 and x<=right and top<=y<=bottom or
                    mask&2 and x>=left and top<=y<=bottom)
        for y in range(16):
            for x in range(8):
                if not metal(x,y):continue
                # Broad, dark plate. The lower/right silhouette is a cast shadow.
                p[y][x] = 3
                if not metal(x,y-1) or not metal(x-1,y):p[y][x] = 2
                if not metal(x+1,y) or not metal(x,y+1):p[y][x] = 0
        k = kind&15
        if a:
            # One recess per authored section; most plates remain unmarked.
            if k == 2 and mask == 10:
                c.rect(p,2,5,4,5,0);c.line(p,2,10,5,10,2)
                p[6][2]=1;p[6][3]=1
            elif k == 2 and mask == 5:
                c.rect(p,2,5,2,5,0);p[5][2]=1
            elif k == 3:
                if mask == 10:
                    c.line(p,0,8,7,8,0);c.line(p,0,9,7,9,2)
                    if kind&16:c.line(p,1,7,1,10,3)
                    if kind&32:c.line(p,6,7,6,10,3)
                elif mask == 5:
                    c.line(p,3,0,3,15,0)
                    if kind&16:c.line(p,2,2,4,2,2)
                    if kind&32:c.line(p,2,13,4,13,2)
            elif k == 1:
                if mask == 10:c.line(p,5,4,5,11,0)
                elif mask == 5:c.line(p,2,11,4,11,0)
        else:
            # A load-bearing rib with a recessed spine, unlike A's solid slabs.
            if mask == 10:
                c.line(p,0,7,7,7,0);c.line(p,0,10,7,10,0)
                if k in (1,4):
                    c.rect(p,2,4,2,7,2);c.line(p,3,5,3,9,3)
                if k == 2:
                    c.rect(p,1,5,5,5,0);c.line(p,1,5,5,5,2)
                    p[7][4]=1
            elif mask == 5:
                c.line(p,3,0,3,15,0)
                if k in (1,4):
                    c.line(p,2,5,4,5,2);c.line(p,2,11,4,11,2)
                elif k == 2:p[7][4]=1
            else:
                # Closed central elbow cap, including free ends and junctions.
                c.rect(p,3,6,2,4,0);c.line(p,2,5,4,5,2)
                if mask == 0:p[7][3]=2
        return c.tile(p)

    def floors(self):
        c=self.c;out=[]
        for n in range(12):
            p=c.blank()
            # Open, low-contrast material strokes, never a closed tile frame.
            if self.direction == 'A':
                c.line(p,0,15,2,15,3)
                if n:c.line(p,5,7,6,7,3)
            else:
                c.line(p,6,14,7,14,3)
                if n:p[6][2]=3
            out.append(c.tile(p))
        return out

    @staticmethod
    def floor_plan(rows,number,specs):
        return {(x,y):1 for y,row in enumerate(rows) for x,ch in enumerate(row)
                if ch in ' $@' and (x+2*y)%4==1}, []

    def container(self,docked=False,phase=None):
        c=self.c;p=c.blank()
        if self.direction=='A':
            c.rect(p,1,2,6,11,3)
            c.line(p,2,1,5,1,1);c.line(p,1,2,5,2,1)
            c.line(p,1,3,1,11,1);c.line(p,2,12,5,12,3)
            c.line(p,2,10,5,10,0)
        else:
            # Beveled transport pod, horizontal shoulder and separate feet.
            c.rect(p,2,1,4,12,3);c.rect(p,1,3,6,8,3)
            c.line(p,2,1,5,1,1);c.line(p,1,3,1,9,1)
            c.line(p,2,2,5,2,1);c.line(p,2,11,5,11,0)
            p[12][2]=p[12][5]=1
        # Shared cargo sign: black inset with warm two-pixel diagonal bolt.
        c.rect(p,2,4,4,6,0)
        for x,y in ((4,4),(3,5),(3,6),(4,6),(4,7),(3,8)):
            p[y][x]=1
        if docked:
            # Persistent cyan latch bar + two feet, visible after flash ends.
            c.line(p,1,14,6,14,2);p[15][1]=p[15][6]=2
            for x,y in ((2,7),(3,8),(4,7),(5,6)):p[y][x]=2
        if phase is not None:p[3+phase*3][6]=2
        return p

    def dock(self):
        c=self.c;p=c.blank()
        for y in (1,14):
            c.line(p,1,y,2,y,2);c.line(p,5,y,6,y,2)
        for x in (1,6):
            c.line(p,x,2,x,4,2);c.line(p,x,11,x,13,2)
        p[7][3]=p[8][4]=1
        return p

    def robot_frames(self):
        # Identity retained: light service chassis, dark visor, tank treads,
        # directional tool arm. 2 substrates x 4 directions x 5 old states.
        frames=[]
        for goal in range(2):
            for direction in range(4):
                for mode in range(5):
                    p=[[0]*8 for _ in range(16)]
                    def rect(x,y,w,h,v):
                        for yy in range(y,y+h):
                            for xx in range(x,x+w):p[yy][xx]=v
                    rect(2,2,4,4,1);rect(1,7,6,5,1)
                    rect(2,4,4,1,0);p[4][3]=2
                    rect(1,11,2,4,2);rect(5,11,2,4,2)
                    rect(3,8,2,2,0)
                    if self.direction=='B':p[2][2]=p[2][5]=0;p[7][1]=p[7][6]=2
                    if direction==0:rect(3,1,2,2,1)
                    elif direction==1:rect(3,5,2,2,1)
                    elif direction==2:rect(6,6,2,2,1)
                    else:rect(0,6,2,2,1)
                    if mode:
                        yy=12+(mode&1);p[yy][1]=p[yy][5]=0
                        if mode>=3:
                            xx,yy=((3,0),(3,6),(7,8),(0,8))[direction]
                            p[yy][xx]=2
                    if goal:
                        for x in (1,2,5,6):p[0][x]=p[15][x]=2
                    frames.extend(encode_tile(p))
        assert len(frames)==1280
        return bytes(frames)

    def device(self,kind,phase):
        c=self.c
        w,h={'terminal':(16,32),'cabinet':(16,48),'fan':(16,32),
             'gate':(24,32),'installation':(32,32)}[kind]
        p=c.blank(w,h);a=self.direction=='A'
        # Common mounting envelope and right-side service socket, all phases.
        c.rect(p,1,2,w-2,h-4,3)
        c.line(p,2,1,w-3,1,2);c.line(p,1,2,1,h-4,2)
        if not a:
            # Shoulder cutouts and two structural ribs unify B's machinery.
            c.rect(p,1,2,2,3,0);c.rect(p,w-3,h-6,2,3,0)
            for x in (3,w-4):c.line(p,x,4,x,h-5,2)
        if kind in ('terminal','cabinet'):
            tops=[6] if kind=='terminal' else [6,20,34]
            for y in tops:
                c.rect(p,4,y,w-8,9,0)
                c.line(p,4,y,w-5,y,2)
                c.line(p,5,y+3,w-6,y+3,3)
                p[y+5][5+phase]=2
            if kind=='terminal':
                c.rect(p,4,22,8,4,0);c.line(p,5,23,10,23,3)
        elif kind=='fan':
            # Recessed rotor, same existing two-orientation period sequence.
            c.rect(p,4,6,8,20,0)
            c.line(p,5,6,10,6,2);c.line(p,5,25,10,25,3)
            if phase&1:
                c.line(p,5,9,10,22,2);c.line(p,10,9,5,22,2)
            else:
                c.line(p,7,8,8,23,2);c.line(p,4,15,11,16,2)
            c.rect(p,7,14,2,3,3)
        elif kind=='gate':
            c.rect(p,4,6,w-8,h-12,0)
            for x in ((6,12,18) if a else (5,9,14,18)):
                c.line(p,x,7,x,h-8,3 if a else 2)
            c.line(p,4,7,w-5,7,2)
            c.rect(p,w//2-1,14,2,4,3)
        else:
            c.rect(p,4,6,w-8,7,0);c.line(p,4,6,w-5,6,2)
            c.line(p,5,10,w-6,10,3);p[9][5+phase*6]=2
            if a:
                c.rect(p,4,17,w-8,9,0)
                for x in (6,12,18,24):c.line(p,x,18,x,24,3)
            else:
                for x in (5,12,19,26):
                    c.rect(p,x,17,2,9,2);c.line(p,x+2,18,x+2,25,0)
        c.line(p,w-3,h//2,w-1,h//2,3)
        return p
