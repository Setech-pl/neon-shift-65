"""One offline cosmetic pass over FINISH1; fixed geometry and asset sizes."""

def install(c):
    previous_device=c.device
    def device(kind,phase):
        p=previous_device(kind,phase)
        # Remove the broad bright face. Keep the exact outline, small controls,
        # rotor/conduit strokes and every original zero aperture.
        variants=[previous_device(kind,i) for i in range(4)]
        for y in range(2,len(p)-2):
            for x in range(2,len(p[0])-2):
                if all(v[yy][xx]==2 for v in variants for yy,xx in
                     ((y,x),(y-1,x),(y+1,x),(y,x-1),(y,x+1))):p[y][x]=0
        return p
    c.device=device
    # A sparse paired floor mark is present even on the plain floor variant;
    # wall apertures remain black, ambient fragments remain PF3 gray.
    def floors():
        result=[]
        for k in range(12):
            p=c.blank();x=1+k%4;y=3+(k//4)*4
            c.line(p,x,y,x+1,y,3)
            result.append(c.tile(p))
        assert len(set(result))==12
        return result
    c.floors=floors
    c.decoration.VARIANT='FINISH2-muted-devices-readable-floor'
