"""PMG1 code-native tiles and masks; same 8 color clocks x 16 scanlines."""
import json, struct
from warehouses import crc16

PALETTES=[234,186,74,58]

def tile(p):
    return bytes(sum(p[y+dy][x+dx] << (6-2*dx) for dx in range(4))
                 for y,x in ((0,0),(0,4),(8,0),(8,4)) for dy in range(8))

def canvas():return [[0]*8 for _ in range(16)]
def rect(p,x,y,w,h,c):
    for yy in range(y,y+h):
        for xx in range(x,x+w):p[yy][xx]=c

def wall(mask):
    p=canvas();rect(p,0,0,8,16,3)
    rect(p,2,7,4,1,0);p[3][2]=0;p[11][5]=0
    # Joined steel panels: subdued bevel, seams only at exposed edges.
    if not mask&1:rect(p,0,0,8,1,2);rect(p,1,1,6,1,0)
    if not mask&2:rect(p,7,0,1,16,0)
    if not mask&4:rect(p,0,14,8,2,0)
    if not mask&8:rect(p,0,0,1,16,0)
    if not mask&1 and not mask&8:p[2][1]=2
    if not mask&4 and not mask&2:p[12][6]=2
    return p

def dock():
    p=canvas()
    for x in (0,6):
        rect(p,x,2,2,1,2);rect(p,x,13,2,1,2)
    for x in (0,7):rect(p,x,3,1,3,2);rect(p,x,10,1,3,2)
    rect(p,3,7,2,2,2)
    return p

def crate(on=False):
    p=canvas();rect(p,1,2,6,12,3);rect(p,2,3,4,1,2)
    # Broad steel mass, unmistakable lightning rune cut into the panel.
    for y,xs in ((5,(4,5)),(6,(3,4)),(7,(2,3,4,5)),(8,(4,)),(9,(3,4)),(10,(2,3))):
        for x in xs:p[y][x]=2
    rect(p,2,12,4,1,0)
    if on:
        for x in (0,7):rect(p,x,0,1,3,2);rect(p,x,13,1,3,2)
    return p

def frames():
    result=bytearray()
    for facing in range(4):
        for pose in range(5):
            p=canvas()
            rect(p,2,1,4,2,1);rect(p,1,3,6,8,1)
            rect(p,2,11,4,1,1)
            # Four different visor orientations. Both masks have holes;
            # P0 always wins overlap, so accents never rely on OR priority.
            if facing==0:rect(p,2,2,4,2,2);rect(p,3,5,2,2,0)
            elif facing==1:rect(p,2,7,4,2,2);rect(p,3,3,2,2,0)
            elif facing==2:rect(p,4,4,3,3,2);p[5][6]=0
            else:rect(p,1,4,3,3,2);p[5][1]=0
            for x in (0,6):
                rect(p,x,11,2,4,1)
                p[12+(pose==2 or pose==4)][x]=0
            if pose>=3:
                if facing in (0,1):rect(p,0,0 if facing==0 else 14,2,2,2);rect(p,6,0 if facing==0 else 14,2,2,2)
                else:rect(p,7 if facing==2 else 0,8,1,3,2)
            for color in (1,2):result.extend(sum((p[y][x]==color)<<(7-x) for x in range(8)) for y in range(16))
    assert len(result)==640
    return bytes(result)

def package(sections):
    body=b''.join(b for _,b in sections);hdr=bytearray(144)
    hdr[:8]=b'NSRQ'+bytes([3,1,len(sections),0])
    struct.pack_into('<HH',hdr,8,len(body),crc16(body));off=0
    for i,(addr,b) in enumerate(sections):
        struct.pack_into('<4H',hdr,16+8*i,addr,len(b),off,crc16(b));off+=len(b)
    struct.pack_into('<H',hdr,12,crc16(hdr[16:]));struct.pack_into('<H',hdr,14,crc16(hdr[:14]))
    return bytes(hdr)+body

def bind_overlay(asset,code):
    assert len(code)==2048 and asset[4]==3
    sections=[]
    for i in range(asset[6]):
        addr,n,off,_=struct.unpack_from('<4H',asset,16+8*i)
        sections.append((addr,code if addr==0xa000 else asset[144+off:144+off+n]))
    return package(sections)

def install(c):
    def scene(level,number,a):
        rows=level['rows'];w=len(rows[0]);h=len(rows);vw,vh=level.get('visual_size',(w,h))
        # Keep logical padding, move the original authored rectangle only.
        bx=20-vw;by=13-vh
        font=[bytes(8)];index={font[0]:0}
        def codes(p):
            raw=tile(p);r=[]
            for q in range(4):
                b=raw[q*8:q*8+8]
                if b not in index:index[b]=len(font);font.append(b)
                r.append(index[b]|128)
            return r
        floor=codes(canvas());walls=[codes(wall(m)) for m in range(16)]
        objects=[codes(crate()),codes(crate(True)),codes(dock())]
        screen=bytearray(880);comp=bytearray(800)
        for y in range(h):
            for x in range(w):
                inside=x<vw and y<vh
                if inside and rows[y][x]=='#':
                    mask=sum(v for dx,dy,v in ((0,-1,1),(1,0,2),(0,1,4),(-1,0,8)) if 0<=x+dx<vw and 0<=y+dy<vh and rows[y+dy][x+dx]=='#')
                    cc=walls[mask]
                else:cc=floor
                comp[(y*20+x)*4:(y*20+x)*4+4]=bytes(cc)
                if inside:
                    for q,v in enumerate(cc):screen[(by+2*y+q//2)*40+bx+2*x+q%2-80]=v
        assert len(font)<=124,len(font)
        charset=b''.join(font)+bytes(1024-len(font)*8)
        desc=bytearray(544);desc[:8]=bytes([w,h,bx,by,0,number,c.themes.AREA,1])
        desc[8:128]=bytes(v for _ in range(5) for cc in objects+objects[1:2]*3 for v in cc)
        desc[536:541]=bytes([238,PALETTES[c.themes.AREA-1],2,6,0])
        # Bounds are explicit format-v3 metadata. Validator checks padding.
        desc[541:544]=bytes([vw,vh,3])
        sections=[(0x8c00,charset),(0xa000,bytes(2048)),(0x9800,bytes(screen)),(0x1400,bytes(comp)),(0xb160,frames()),(0x9de0,bytes(desc))]
        data=package(sections);path=c.OUT/f'scene-{number}.nrq';path.write_bytes(data)
        (c.OUT/f'scene-{number}-pmg1.json').write_text(json.dumps(dict(visual=[vw,vh],logical=[w,h],origin_chars=[bx,by],glyphs=len(font),scale=[8,16],robot='P0/P1, one scanline',palette=[238,PALETTES[c.themes.AREA-1],2,6,0]),indent=2)+'\n')
        return dict(name='scene-'+str(number),kind=number+1,bytes=len(data),raw=len(data)-144,sections=[dict(address=addr,size=len(b)) for addr,b in sections])
    c.scene=scene
