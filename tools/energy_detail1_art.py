"""Offline Energy pixels only. ANTIC4 inks, unchanged geometry and PMG.

PF0 copper $28 replaces unused cargo ink $EE; cargo actually uses PF1/PF3.
PMG robot colors are separate hardware registers. No renderer modifications.
"""

def install(c):
    if c.themes.AREA != 1:
        return None
    c.decoration.devices = lambda specs, number, level: []
    c.decoration.wall_kind = lambda mask, x, y, n: (1 if (x if mask == 10 else y) % 3 == 0 else 0)

    def wall(mask, kind=0):
        p=c.blank()
        c.rect(p,2,4,4,8,1)
        for bit,x,y,w,h in ((1,2,0,4,6),(2,4,4,4,8),(4,2,10,4,6),(8,0,4,4,8)):
            if mask & bit:c.rect(p,x,y,w,h,1)
        solid=[[bool(v) for v in row] for row in p]
        for y in range(16):
            for x in range(8):
                if not solid[y][x]:continue
                if y==15 or not solid[y+1][x] or x==7 and not mask&2 or x<7 and not solid[y][x+1]:p[y][x]=3
                elif y==0 and not mask&1 or y>0 and not solid[y-1][x]:p[y][x]=3
        # Joints occur once per panel, rather than one hatch on every tile.
        if mask==10 and kind:
            c.line(p,0,5,0,10,0);c.line(p,1,5,1,10,3)
            p[6][2]=3
        elif mask==5 and kind:
            c.line(p,3,0,4,0,0);c.line(p,3,1,4,1,3)
        elif mask not in (5,10,15):
            # Recessed hub closes elbows and tees without opening to floor.
            c.rect(p,3,6,2,4,0);c.line(p,3,6,4,6,3)
        elif mask==15:
            c.rect(p,3,6,2,4,3)
        return c.tile(p)
    c.wall=wall
    return Background(c)

class Background:
    def __init__(self,c):self.c=c

    def image(self,level):
        c=self.c;p=c.blank(160,192)
        R=lambda x,y,w,h,v:c.rect(p,x,y,w,h,v)
        L=lambda x,y,xx,yy,v:c.line(p,x,y,xx,yy,v)
        def housing(x,y,w,h):
            R(x,y,w,h,3);R(x+1,y+2,w-3,h-4,1)
            L(x+1,y+1,x+w-3,y+1,3)
            L(x+w-2,y+3,x+w-2,y+h-2,0)
            L(x+1,y+h-2,x+w-3,y+h-2,0)
        # Left cabinet: separate side, rebated door, hinges and handle.
        housing(1,64,13,56)
        R(3,69,8,43,0);R(4,70,6,40,3)
        L(10,70,10,110,1)
        for y in (73,101):R(2,y,2,4,3)
        R(8,87,1,7,0);R(9,87,1,2,1)
        R(5,75,3,8,0);L(6,76,6,80,1)
        R(4,115,7,2,0)
        # Lamp hood, glass, neck, cable with two clips and socket.
        R(3,32,8,2,3);R(2,34,10,3,1);R(3,37,8,3,3)
        R(4,40,6,2,1);L(7,42,7,60,3)
        R(6,47,3,2,1);R(6,55,3,2,1);R(5,61,5,3,3)
        # Quiet overhead supply trunk and a single inspection box.
        L(16,25,143,25,3);L(16,28,143,28,3)
        R(64,22,12,10,3);R(65,24,9,6,0);R(67,26,3,2,1)
        L(144,25,151,32,3);L(144,28,149,33,3)
        vw,vh=level['visual_size'];right=16+vw*8
        if right<=120:
            # Large right installation, entirely outside the authored board.
            x=right+8;w=152-x
            housing(x,48,w,32)
            R(x+3,54,w-8,15,0);L(x+4,66,x+w-7,66,3)
            L(x+5,63,x+8,58,1);L(x+8,58,x+11,63,1)
            R(x+4,73,3,2,3);R(x+w-8,73,3,2,1)
            # Bolted conduit with couplers; links cabinet to junction module.
            L(x+6,81,x+6,96,3);L(x+8,81,x+8,96,1)
            R(x+5,85,5,2,3);R(x+5,93,5,2,3)
            housing(x,100,w,32);R(x+3,105,w-8,20,0)
            for dx in range(4,w-7,5):
                L(x+dx,108,x+dx,121,3)
            L(x+3,115,x+w-6,115,1)
            # Insulated pipe drops to a different lower distribution unit.
            L(x+w-5,133,x+w-5,145,3);L(x+w-7,133,x+w-7,145,1)
            housing(x,148,w,16);R(x+3,152,w-8,7,0)
            for dx in range(4,w-8,8):R(x+dx,154,3,2,3)
        else:
            # Full-size maps keep a narrow service riser in the 16px margin.
            L(151,48,151,153,3);L(153,48,153,153,1)
            for y in (56,104,144):R(149,y,7,3,3)
            housing(148,72,9,24);R(150,77,4,12,0);R(151,80,2,4,1)
        # Bottom: one louvered cooler, one junction box, one pipe manifold.
        # Distinct functions separated by generous unmarked spans.
        housing(20,176,24,14)
        for y in (180,184):L(23,y,39,y,0)
        housing(64,176,16,14);R(67,180,8,6,0);R(69,182,3,2,1)
        L(96,181,135,181,3);L(96,185,135,185,1)
        for x in (100,120,132):R(x,178,2,10,3)
        # No raster artwork may spill into puzzle cells, HUD or bottom margin.
        for y in range(40,40+vh*16):
            for x in range(16,right):p[y][x]=0
        return p

    def glyph(self,p,pos):
        row,col=divmod(pos,40)
        return bytes(sum(p[row*8+y][col*4+x]<<(6-2*x) for x in range(4)) for y in range(8))
