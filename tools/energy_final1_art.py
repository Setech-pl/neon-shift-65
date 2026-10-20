"""Energy-only metal/servicing pass, using ANTIC4 character PF2/PF3 selection.

No runtime drawing, random textures, new font banks or object recoloring.
"""
from energy_detail1_art import Background as DetailBackground

def install(c):
    if c.themes.AREA!=1:return None
    c.decoration.wall_kind=lambda mask,x,y,n: int((x+3*y+n)%7==0)
    def wall(mask,kind=0):
        p=c.blank();c.rect(p,0,0,8,16,3)
        # Full structural mass closes the former repeated four-way apertures.
        # Only boundaries against walkable floor are recessed, NW lighting.
        if not mask&1:c.line(p,0,0,7,0,0)
        if not mask&8:c.line(p,0,0,0,15,0)
        if not mask&2:c.line(p,7,0,7,15,0)
        if not mask&4:c.rect(p,0,14,8,2,0)
        # Sparse keyed joints, no bright frame around individual cells.
        if kind and mask==10:
            c.line(p,0,3,0,11,0);p[4][1]=3
            c.line(p,2,3,3,3,1)
        elif kind and mask==5:
            c.line(p,2,0,5,0,0);p[1][2]=3
        if kind and mask==15:
            c.line(p,0,7,3,7,0);p[6][1]=3
        if kind and not mask&1:
            c.line(p,2,3,4,3,1)
        return c.tile(p)
    c.wall=wall
    return Background(c)

class Background(DetailBackground):
    def image(self,level):
        p=super().image(level);c=self.c
        # Keep all authored equipment geometry, fasteners and cable routes.
        # Former copper faces become dark steel. Outlines/ribs stay legible.
        p=[[4 if v==1 else v for v in row] for row in p]
        R=lambda x,y,w,h,v:c.rect(p,x,y,w,h,v)
        L=lambda x,y,xx,yy,v:c.line(p,x,y,xx,yy,v)
        # Small yellow service labels, glass and indicators, never broad frames.
        R(5,36,4,2,1);R(9,87,1,2,1);L(6,76,6,80,1)
        R(67,26,3,2,1)
        vw,vh=level['visual_size'];right=16+vw*8
        if right<=120:
            x=right+8;w=152-x
            L(x+5,63,x+8,58,1);L(x+8,58,x+11,63,1)
            R(x+w-8,73,3,2,1)
            R(x+4,103,3,1,1);R(x+4,150,3,1,1)
        else:R(151,80,2,4,1)
        R(69,182,3,2,1)
        self.p=p
        return p

    def selector(self,level,row,col):
        bx,by=4,5;vw,vh=level['visual_size']
        if by<=row<by+vh*2 and bx<=col<bx+vw*2:
            x=(col-bx)//2;y=(row-by)//2
            if level['rows'][y][x]=='#':
                # Exposed north face is medium steel; structure below graphite.
                top=y==0 or level['rows'][y-1][x]!='#'
                return 128 if top and (row-by)%2==0 else 0
            return 128
        # One gray per character is a real ANTIC4 limit. At mixed contour/body
        # glyphs use graphite throughout; isolated ribs/controls retain medium steel.
        body=any(self.p[row*8+y][col*4+x]==4 for y in range(8) for x in range(4))
        return 128 if row in (4,6,8,12,18,22) or not body else 0

    def glyph(self,p,pos):
        row,col=divmod(pos,40);pixels=[p[row*8+y][col*4+x] for y in range(8) for x in range(4)]
        values=[(0 if row in (4,6,8,12,18,22) and 3 in pixels else 3) if v==4 else v for v in pixels]
        return bytes(sum(values[y*4+x]<<(6-2*x) for x in range(4)) for y in range(8))
