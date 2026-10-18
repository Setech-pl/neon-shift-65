"""Offline refinement of areas 2–4, preserving the existing bitmap compiler."""
def install(c):
    if c.themes.AREA==1:return
    previous=c.wall
    def wall(mask,kind=0):
        p=c.decode_tile(previous(mask,0))
        if kind and mask in (5,10):
            if c.themes.AREA==2:
                # Industrial hose couplings, with a dark inspection aperture.
                c.line(p,2,5,5,5,2);c.line(p,2,10,5,10,2)
                p[7][3]=1;p[9][4]=0
            elif c.themes.AREA==3:
                # Server tray face: bolts and inset connector, within metal.
                p[5][2]=1;p[10][5]=1;c.line(p,3,8,4,8,2)
            else:
                # Reactor shield fasteners and a recessed thermal slit.
                p[5][2]=1;p[10][5]=1;c.line(p,3,7,4,7,0)
        return c.tile(p)
    c.wall=wall
    c.decoration.wall_kind=lambda mask,x,y,number:int(mask in (5,10) and (x+2*y)%4<2)
