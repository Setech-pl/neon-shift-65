"""NEON-AREAS1 offline artwork and per-level PMG data, no new raster modes.

Descriptor 160..257: core[32], shell[32], scan sequence[32], P2/P3 colors.
Only this level's data is resident. Native tube footprint remains 16x32.
"""
from energy_final1_art import Background as SteelBackground
from energy_fix1_ambient import descriptors as energy_descriptors

COLORS={1:(0x9e,0x96),2:(0xbe,0xb6),3:(0x4e,0x46),4:(0x2c,0x28)}

def neon_data(area):
    if area==1:
        core=[6,6,12,12,12,24,24,24,48,48,48,96,96,126,126,6,
              6,12,12,12,24,24,24,48,48,48,96,96,64,64,0,0]
        shell=[15,15,30,30,30,60,60,60,120,120,120,240,240,255,255,15,
               15,30,30,30,60,60,60,120,120,120,240,240,224,224,64,0]
        sequence=list(range(32))
    elif area==2:
        # Stem, opposed pairs of leaves, and a rooted laboratory tray.
        core=[0,0,0x10,0x10,0x10,0x12,0x16,0x1c,0x18,0x10,0x10,0x50,
              0x70,0x30,0x10,0x10,0x12,0x16,0x1c,0x18,0x10,0x50,0x70,0x30,
              0x10,0x10,0x10,0x10,0x7e,0x42,0x7e,0]
        shell=[0,0x10,0x38,0x38,0x18,0x17,0x1f,0x1e,0x1c,0x18,0xd0,0xf0,
               0xf0,0x70,0x30,0x18,0x17,0x1f,0x1e,0x1c,0x18,0xd0,0xf0,0x70,
               0x30,0x38,0x38,0x10,0x7e,0x7e,0x7e,0]
        sequence=list(range(31,-1,-1))
    elif area==3:
        # Three nodes connected by a stepped transmission route.
        core=[0,0,0x60,0x60,0x60,0x60,0x20,0x20,0x20,0x3c,0x04,0x04,
              0x0e,0x0a,0x0a,0x0e,0x04,0x04,0x04,0x3c,0x20,0x20,0x20,0x20,
              0x60,0x60,0x60,0x60,0,0,0,0]
        shell=[0,0xf0,0xf0,0xf0,0xf0,0xf0,0x70,0x70,0x7c,0x7e,0x0e,0x0e,
               0x1f,0x1b,0x1b,0x1f,0x0e,0x0e,0x3e,0x7e,0x70,0x70,0x70,0x70,
               0xf0,0xf0,0xf0,0xf0,0xf0,0,0,0]
        sequence=[r for r in (1,5,8,12,16,19,23,25) for _ in range(4)]
    else:
        # Armored vertical chamber with three bright segmented core windows.
        core=[0,0x18,0x3c,0x24,0x24,0x24,0x3c,0x24,0x24,0x24,0x3c,0x24,
              0x24,0x24,0x3c,0x24,0x24,0x24,0x3c,0x24,0x24,0x24,0x3c,0x24,
              0x24,0x24,0x3c,0x24,0x3c,0x18,0,0]
        shell=[0x18,0x3c,0x7e,0x66,0x66,0x66,0x7e,0x66,0x66,0x66,0x7e,0x66,
               0x66,0x66,0x7e,0x66,0x66,0x66,0x7e,0x66,0x66,0x66,0x7e,0x66,
               0x66,0x66,0x7e,0x66,0x7e,0x3c,0x18,0]
        sequence=list(range(16))+list(range(15,-1,-1))
    assert len(core)==len(shell)==len(sequence)==32
    assert all(a&b==a for a,b in zip(core,shell))
    return bytes(core+shell+sequence+list(COLORS[area]))

def install(c, energy):
    area=c.themes.AREA
    c.decoration.devices=lambda specs,number,level:[]
    # Two keyed variants; the unmarked face remains predominant.
    c.decoration.wall_kind=lambda mask,x,y,n: 1 if (x+3*y+n)%5==0 else 2 if (3*x+y+n)%11==0 else 0
    def wall(mask,kind=0):
        p=c.blank();c.rect(p,0,0,8,16,3)
        if not mask&1:c.line(p,0,0,7,0,0)
        if not mask&8:c.line(p,0,0,0,15,0)
        if not mask&2:c.line(p,7,0,7,15,0)
        if not mask&4:c.rect(p,0,14,8,2,0)
        # Inset keyed joins leave the structural silhouette intact.
        if mask==10 and kind:
            c.line(p,3,3,3,12,0);p[4][4]=3
            if kind==2:p[10][5]=0
        elif mask==5 and kind:
            c.line(p,2,7,5,7,0);p[6][2]=3
        elif mask==15 and kind:
            c.line(p,1,7,5,7,0);c.line(p,5,7,5,11,0)
        elif kind:
            c.line(p,2,5,4,5,0);p[6][2]=0
        if kind==1 and not mask&1:
            c.line(p,2,3,3,3,1)  # sparse yellow service tab
        if area==2 and kind==2:
            c.rect(p,3,6,2,3,0);c.line(p,3,6,4,6,3)
        elif area==3 and kind==2:
            c.line(p,2,9,5,9,0);c.line(p,2,11,5,11,0)
        elif area==4 and kind==2:
            c.line(p,2,4,2,11,0);c.line(p,5,4,5,11,0)
        return c.tile(p)
    c.wall=wall
    return energy if area==1 else Background(c)

class Background(SteelBackground):
    def image(self,level):
        p=super().image(level);c=self.c;area=c.themes.AREA
        R=lambda x,y,w,h,v:c.rect(p,x,y,w,h,v)
        L=lambda x,y,xx,yy,v:c.line(p,x,y,xx,yy,v)
        # Shared physical mounting bay, different surrounding equipment.
        R(4,70,7,40,0)
        vw,vh=level['visual_size'];right=16+vw*8
        if right<=120:
            x=right+8;w=152-x
            R(x+3,105,w-8,20,0)
            if area==2:
                # Glass growth vessels, steel caps, feed/return pipes.
                for dx in range(4,w-7,7):
                    R(x+dx,107,5,16,3);R(x+dx+1,110,3,10,0)
                    R(x+dx+2,115,1,5,1)
                    L(x+dx+1,114,x+dx+3,112,3)
            elif area==3:
                for yy in (108,114,120):
                    L(x+4,yy,x+w-7,yy,3)
                    R(x+5,yy+1,2,1,1)
                    R(x+w-9,yy+1,2,1,1)
            else:
                for dx in range(4,w-7,4):
                    R(x+dx,107,2,16,3)
                L(x+3,115,x+w-6,115,1)
        # Bottom installation: tank/manifold, server vents, or cooling ribs.
        R(23,180,17,7,0)
        if area==2:
            L(23,185,39,185,3);R(26,181,3,4,3);R(34,181,3,4,3)
        elif area==3:
            for yy in (180,183,186):L(23,yy,39,yy,3)
        else:
            for xx in (24,28,32,36):R(xx,180,2,7,3)
        device_phase(c,p,level,0)
        self.p=p
        return p

def device_phase(c,p,level,phase):
    """Four authored poses, exact same four screen cells as Energy's cache."""
    area=c.themes.AREA;vw,vh=level['visual_size']
    R=lambda x,y,w,h,v:c.rect(p,x,y,w,h,v)
    if vw<=13:
        x=24+vw*8
        R(x+5,58,7,6,0)
        if area==2:
            for dx in (5,9):
                R(x+dx,58,3,6,3);R(x+dx+1,59,1,4,0)
                R(x+dx+1,63-(phase%3+1),1,phase%3+1,1)
        elif area==3:
            for i,dx in enumerate((5,9)):
                for j,yy in enumerate((58,60,62)):
                    R(x+dx,yy,3,1,1 if (phase+i)%3==j else 3)
        else:
            for j,yy in enumerate((58,60,62)):
                R(x+5,yy,7,1,1 if j<=((0,1,2,1)[phase]) else 3)
    else:
        for i,xx in enumerate((151,152)):
            for j,yy in enumerate(range(80,84)):
                if area==3:lit=(phase+i)%4==j
                else:lit=j>=4-(1,2,4,2)[phase]
                p[yy][xx]=1 if lit else 0
    for yy in (182,183):
        for xx in (69,70,71):p[yy][xx]=1 if phase<2 else 3
    for i,xx in enumerate(range(32,36)):
        p[180][xx]=1 if ((i+phase)%4<2 if area==3 else i<=(0,1,3,1)[phase]) else 3

def descriptors(background,level,fonts,screen):
    # Energy's four accepted local effects remain pixel/period compatible.
    if background.c.themes.AREA==1:
        return energy_descriptors(background,level,fonts,screen)
    original=background.image(level);variants=[[row[:] for row in original] for _ in range(4)]
    for phase,p in enumerate(variants):device_phase(background.c,p,level,phase)
    vw,vh=level['visual_size']
    positions=[(7,7+2*vw),(7,8+2*vw)] if vw<=13 else [(10,37),(10,38)]
    positions += [(22,17),(22,8)]
    result=[];metadata=[]
    for slot,(row,col) in enumerate(positions):
        bank=0 if row<13 else 1;codes=[];selector=background.selector(level,row,col)
        for phase,p in enumerate(variants):
            glyph=background.glyph(p,row*40+col)
            if phase==0:
                code=screen[(row-2)*40+col]
                assert fonts[bank][code&127]==glyph and code&128==selector
            else:
                try:index=fonts[bank].index(glyph)
                except ValueError:
                    index=len(fonts[bank]);assert index<124
                    fonts[bank].append(glyph)
                code=index|selector
            codes.append(code)
        assert len(set(codes))>1,(level['number'],slot)
        period=36 if slot<2 else 50 if slot==2 else 13;addr=0x8800+row*40+col
        result.append(bytes((addr&255,addr>>8,period,0,*codes)))
        metadata.append(dict(role=('liquid' if background.c.themes.AREA==2 else 'activity' if background.c.themes.AREA==3 else 'core-meter') if slot<2 else 'control' if slot==2 else 'segments',
                             row=row,col=col,address=addr,period=period,codes=codes,native_box=[8+col*8,24+row*8,8,8]))
    return b''.join(result),metadata

def install_runtime(source):
    p=source/'validate.c';s=p.read_text()
    s=s.replace('count!=(DESC[6]==1?4:0)','count!=4')
    s=s.replace('for(n=128+(unsigned int)count*8;n<536;n++)', 'for(n=258;n<536;n++)')
    p.write_text(s)
    p=source/'hardware.s';s=p.read_text()
    # Remove Energy-only guards; all four areas use the same DMA resources.
    a=s.index('neon_dma:\n');b=s.index('neon_prepare:\n',a)
    s=s[:a]+'neon_dma:\n    lda #$3e\n    rts\n'+s[b:]
    guard='    lda $9de6\n    cmp #1\n    bne @done\n'
    assert s.count(guard)==2;s=s.replace(guard,'')
    s=s.replace('lda #$9e\n    sta $d014','lda $9de0+256\n    sta $d014')
    s=s.replace('lda #$96\n    sta $d015','lda $9de0+257\n    sta $d015')
    s=s.replace('    ldx neon_head\n    ldy #3','    ldx neon_head\n    lda neon_sequence,x\n    and #31\n    tax\n    ldy #3')
    s=s.replace('    sta neon_head\n    tax\n    ldy #3','    sta neon_head\n    tax\n    lda neon_sequence,x\n    and #31\n    tax\n    ldy #3')
    a=s.index('.segment "RODATA"\n; Normal player width:')
    s=s[:a]+'''neon_core = $9de0+160
neon_shell = $9de0+192
neon_sequence = $9de0+224
'''
    p.write_text(s)
