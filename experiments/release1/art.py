"""One final offline pass over RC2; no runtime or resource layout changes."""

def install(c):
    area=c.themes.AREA
    palette=list(c.themes.SPEC['palette'])
    # Dark brass / green / fuchsia / red. PF0 cargo and PF3 ambient stay fixed.
    palette[1]={1:0xea,2:0xba,3:0x4a,4:0x3a}[area]
    c.themes.SPEC=dict(c.themes.SPEC,palette=palette)
    previous=c.wall

    def wall(mask,kind=0):
        p=c.decode_tile(previous(mask,kind))
        # Closed junction housing: the small dark inset reads as a service
        # panel, without the open central hole of the old elbow/tee junction.
        if mask not in (5,10):
            c.rect(p,2,5,4,6,2)
            c.line(p,3,7,4,7,3)
            c.line(p,3,9,4,9,2)
        # Every straight variant retains continuous upper/lower or side rails.
        # Vent slits are shallow, enclosed cuts, never a full-width opening.
        if mask==10:
            c.line(p,0,5,7,5,2);c.line(p,0,10,7,10,3)
            if kind==2:
                for x in (1,3,5):c.line(p,x,7,x,8,0)
        elif mask==5:
            c.line(p,2,0,2,15,2);c.line(p,5,0,5,15,3)
        return c.tile(p)

    c.wall=wall
    c.decoration.VARIANT='RELEASE1-closed-metal-four-dominants'
