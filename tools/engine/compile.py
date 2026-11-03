#!/usr/bin/env python3
"""Native ANTIC4 artwork, absolute-raster strip compiler and RAW section packs.

No production assets are overwritten. Static quarters are interned independently;
only four live robot slots are reserved per strip. Animation phases are compiled
only into strips which actually display them. Input pixels, allocation and all
duplicate/cross-strip costs are exported for review.
"""
import hashlib, json, re, struct, sys, os
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))
from assets import encode_tile, decode_tile, png
from warehouses import crc16
from solver import solve_path, parse
from artwork import title_pixels,footer_pixels,container_pixels

OUT = Path(os.environ.get('NEON_ART2_BUILD','build/eng3-observed-input-3pal/area-1'))
BANKS = [0x8c00, 0xa000, 0xa400, 0xa800, 0xac00]
SOURCE = Path(__file__).parent

def arrays():
    text = (OUT/'reference/prototype_assets.c').read_text()
    return {n: bytes(map(int, re.findall(r'\d+', b))) for n,b in
            re.findall(r'const unsigned char (\w+)\[\] = \{(.*?)\};', text, re.S)}

def rect(p,x,y,w,h,c):
    for yy in range(max(0,y),min(len(p),y+h)):
        for xx in range(max(0,x),min(len(p[0]),x+w)): p[yy][xx]=c

def line(p,x,y,xx,yy,c):
    n=max(abs(xx-x),abs(yy-y))
    for i in range(n+1):
        px=x+(xx-x)*i//max(1,n);py=y+(yy-y)*i//max(1,n)
        if 0<=py<len(p) and 0<=px<len(p[0]):p[py][px]=c

def blank(w=8,h=16):return [[0]*w for _ in range(h)]
def tile(p):return bytes(encode_tile(p))

def cool(data):
    # Keep 0/1/2; redirect the formerly blue third pixel to cyan explicitly.
    return bytes(sum((2 if (v>>k)&3==3 else (v>>k)&3)<<k for k in (0,2,4,6)) for v in data)

def floors():
    result=[]
    for k in range(12):
        p=blank()
        # Flat copper joins: no vertical full-height edges or closed frames.
        if k in (1,3):line(p,0,0,3,0,3)
        if k in (2,3):line(p,4,0,7,0,3)
        if k in (4,5):rect(p,2 if k==4 else 6,4,1,1,3)
        if k in (6,7):line(p,2,8 if k==6 else 6,4,8 if k==6 else 6,3)
        if k in (8,9):line(p,1,11 if k==8 else 13,4,11 if k==8 else 13,3)
        if k in (10,11):line(p,2,5 if k==10 else 11,5,5 if k==10 else 11,3)
        result.append(tile(p))
    assert len(set(result))==12
    return result

def wall(mask,kind=0):
    p=blank();rect(p,2,4,4,8,3);rect(p,2,5,4,6,2)
    # Connected arms touch neighbours; outer highlight is a continuous run.
    if mask&1:rect(p,2,0,4,6,3);rect(p,3,0,2,6,2)
    if mask&4:rect(p,2,10,4,6,3);rect(p,3,10,2,6,2)
    if mask&2:rect(p,4,4,4,8,3);rect(p,4,5,4,6,2)
    if mask&8:rect(p,0,4,4,8,3);rect(p,0,5,4,6,2)
    rect(p,2,4,4,1,1 if kind else 2)
    if kind:rect(p,3,8,2,2,0)
    return cool(tile(p))

def device(kind,phase):
    w,h={'terminal':(16,32),'cabinet':(16,48),'fan':(16,32),'gate':(24,32),'installation':(32,32)}[kind]
    p=blank(w,h)
    # Heavy enclosing silhouette means every decorated cell remains a wall.
    rect(p,1,1,w-2,h-2,3);rect(p,2,2,w-4,h-4,2)
    line(p,1,1,w-2,1,1);line(p,1,1,1,h-2,1)
    if kind=='terminal':
        rect(p,3,5,10,13,0);line(p,4,8,11,8,2)
        line(p,4,11,6+phase,11,2);rect(p,4+phase*2,14,1,1,1)
        rect(p,3,23,10,5,0);line(p,4,25,11,25,1)
    elif kind=='cabinet':
        for y in (7,21,35):
            rect(p,3,y,10,8,0);line(p,4,y+2,11,y+2,2)
            rect(p,4+phase*2,y+5,1,1,1)
        line(p,8,2,8,45,3)
    elif kind=='fan':
        rect(p,3,5,10,22,0)
        # Outline and hub fixed; two diagonal/vertical rotor orientations.
        line(p,5,5,10,5,2);line(p,5,26,10,26,2)
        line(p,3,9,3,22,2);line(p,12,9,12,22,2)
        if phase&1:
            line(p,5,8,10,23,2);line(p,10,8,5,23,2)
        else:
            line(p,7,7,8,24,2);line(p,4,15,11,16,2)
        rect(p,7,14,2,4,1)
    elif kind=='gate':
        rect(p,3,5,w-6,h-10,0)
        for x in (5,10,15,20):line(p,x,6,x,25,2)
        line(p,3,16,20,16,1);rect(p,10,13,4,6,3)
    else:
        rect(p,3,7,w-6,6,0);line(p,3,9,w-4,9,2)
        for x in (5,13,21,29):rect(p,x,16,1,11,3)
        rect(p,5+phase*7,9,2,2,1)
    return p

def split(p):
    return {(x//8,y//16):cool(tile([r[x:x+8] for r in p[y:y+16]]))
            for y in range(0,len(p),16) for x in range(0,len(p[0]),8)}

def levels():
    old=json.loads(Path('assets/levels/prototypes.json').read_text())['levels']
    # Padding walls preserves the established REACTOR STORE puzzle exactly.
    medium=dict(name='ENERGY SERVICE BAY',rows=['#'*16]+['#'+r+'##' for r in old[0]['rows']]+['#'*16],
                origin='REACTOR STORE puzzle translated +1,+1; added cells are walls only',track=0)
    maximum=dict(old[1]);maximum['rows']=old[1]['rows'].copy();maximum['name']='SERVICE LOAD 20X10'
    r=list(maximum['rows'][2]);r[18]='*';maximum['rows'][2]=''.join(r)
    if os.environ.get('NEON_ART2_FIXTURE')!='open':
        medium=dict(name='ENERGY SERVICE BAY',rows=(SOURCE/'energy-service-bay-obstacles-v1.xsb').read_text().splitlines(),fixture='energy-service-bay-obstacles-v1',track=0)
    return [medium,maximum,old[2]]

class Strip:
    def __init__(self,i):
        self.i=i;self.data=[bytes(8)];self.index={bytes(8):0};self.refs={};self.conflicts=[]
    def intern(self,b,who,selector=0):
        if b not in self.index:
            code=len(self.data)
            if code>=124:
                self.conflicts.append(dict(owner=who,required=code+1,available=124))
                raise ValueError(f'bank {self.i} overflow at {who}: {code+1}+4 robot slots')
            self.index[b]=code;self.data.append(b)
        code=self.index[b];self.refs.setdefault(code,[]).append(who)
        return code|selector
    def pack(self):return b''.join(self.data)+bytes((124-len(self.data))*8)+bytes(32)

def package(name,sections,kind):
    assert len(sections)<=16
    body=b''.join(b for a,b in sections)
    # Entire fixed section table is protected before any destination is written.
    hdr=bytearray(144);hdr[:4]=b'NSRQ';hdr[4:8]=bytes([2,kind,len(sections),0])
    struct.pack_into('<HH',hdr,8,len(body),crc16(body))
    off=0
    for i,(a,b) in enumerate(sections):
        struct.pack_into('<4H',hdr,16+i*8,a,len(b),off,crc16(b));off+=len(b)
    struct.pack_into('<H',hdr,12,crc16(hdr[16:]))
    struct.pack_into('<H',hdr,14,crc16(hdr[:14]))
    (OUT/(name+'.nrq')).write_bytes(hdr+body)
    return dict(name=name,kind=kind,header=144,raw=len(body),bytes=144+len(body),sections=[dict(address=a,size=len(b),crc16=crc16(b)) for a,b in sections])

def scene(level,number,a):
    rows=level['rows'];w=len(rows[0]);h=len(rows);bx=20-w;by=13-h
    strips=[Strip(i) for i in range(5)]
    # Absolute character rows2..21 form five32-line strips; footer shares4.
    bank=lambda row:min((row-2)//4,4)
    screen=bytearray(880);composition=bytearray(800)
    source=a['scene_maps'][(1 if number==1 else 0)*880:][:880]
    glyphs=a['gameplay_common'][32:]
    background_animations=[];animations=[];owners=[]
    positions=[82,85,723,954,955,956,957]
    for pos,code in enumerate(source,80):
        row=pos//40;col=pos%40
        if bx<=col<bx+2*w and by<=row<by+2*h:continue
        b=strips[bank(row)]
        data=bytes(8) if not code else glyphs[((code&127)-92)*8:((code&127)-91)*8]
        data=bytes(sum((1 if (v>>k)&3==3 else (v>>k)&3)<<k for k in (0,2,4,6)) for v in data)
        data=decoration.background(pos,data,positions)
        screen[pos-80]=b.intern(data,'background',0)
        if pos in positions:
            n=positions.index(pos);phases=[]
            for phase in range(4):
                old=(222 if (phase+n)&3==0 else 220) if n<3 else 252+((n-3)*2+phase)%4
                phase_data=glyphs[((old&127)-92)*8:((old&127)-91)*8]
                phase_data=bytes(sum((1 if (v>>k)&3==3 else (v>>k)&3)<<k for k in (0,2,4,6)) for v in phase_data)
                phases.append(b.intern(phase_data,'background-phase',0))
            background_animations.append((pos,8,0,phases))
    f=floors();objects={}
    dock=cool(a['gameplay_common'][:32])
    object_tiles=[tile(container_pixels()),tile(container_pixels(True)),dock]+[tile(container_pixels(True,n)) for n in range(3)]
    for i,b in enumerate(strips):
        objects[i]=[]
        for n,t in enumerate(object_tiles):
            codes=[]
            for q in range(4):
                reachable=any(rows[y][x]!='#' and bank(by+y*2+q//2)==i for y in range(h) for x in range(w))
                if n in (1,2,3,4,5):reachable=any(rows[y][x] in '.*+' and bank(by+y*2+q//2)==i for y in range(h) for x in range(w))
                codes.append(b.intern(t[q*8:q*8+8],f'object{n}/q{q}',128 if n!=2 else 0) if reachable else 0)
            objects[i].append(codes)
    decorative={};decor_phase={}
    if number==0 and level.get('fixture')=='energy-service-bay-obstacles-v1':
        specs=[('terminal',1,-1,17,0),('cabinet',15,1,31,7),('fan',4,7,6,0),('fan',11,7,9,3),('gate',10,-1,19,0),('installation',6,-1,11,4)]
    elif number==0:
        specs=[('terminal',1,0,17,0),('cabinet',14,1,31,7),('fan',4,6,6,0),('fan',11,6,9,3),('gate',10,0,19,0),('installation',6,0,11,4)]
    elif number==1:
        specs=[]
    else:specs=[]
    original_specs=specs
    specs=decoration.devices(specs,number,level)
    original_cells=[];original_for_cell={}
    for old,new in zip(original_specs,specs):
        for dx,dy in split(device(old[0],0)):
            oldpos=(old[1]+dx,old[2]+dy);newpos=(new[1]+dx,new[2]+dy)
            original_cells.append(oldpos);original_for_cell[newpos]=oldpos
    original_order={(x,y):y*w+x for y in range(h) for x in range(w)}
    for pos in original_cells:
        if pos not in original_order:original_order[pos]=len(original_order)
    animation_order=[]
    floor_selection,floor_anchors=decoration.floor_plan(rows,number,specs)
    for kind,x,y,period,phase in specs:
        variants=[split(device(kind,i)) for i in range(4)]
        for (dx,dy),data in variants[0].items():
            assert not (0<=y+dy<h and 0<=x+dx<w) or rows[y+dy][x+dx]=='#',(kind,x+dx,y+dy,'decor must remain wall')
            assert (x+dx,y+dy) not in decorative,'overlapping device'
            decorative[x+dx,y+dy]=data
            decor_phase[x+dx,y+dy]=(kind,period,phase,[v[dx,dy] for v in variants])
        owners.append(dict(kind=kind,x=x,y=y,width=len(device(kind,0)[0])//8,height=len(device(kind,0))//16,period=period,phase=phase&3,source_phase=phase))
    if number==1:
        # Twelve independent service indicators compete in the same absolute
        # strip. Different cabinet identifications prevent accidental merging
        # of their phase glyphs; each cell remains an existing logical wall.
        for k in range(12):
            variants=[]
            for phase in range(4):
                p=decode_tile(wall(10));rect(p,4,0,4,8,0)
                line(p,4,0,7,0,2);line(p,4,7,7,7,2)
                for bit in range(4):p[5][4+bit]=2 if k&(1<<bit) else 0
                p[2][4+phase]=1
                # All32 descriptors are exercised with ten boxes/large HUD:
                #12 paired indicator fragments plus two extra lower lamps.
                p[10][4+phase]=1
                if k<2:p[10][phase]=1
                variants.append(cool(tile(p)))
            decorative[k+2,0]=variants[0]
            decor_phase[k+2,0]=('stress-indicator',6,k%4,variants)
            owners.append(dict(kind='stress-indicator',x=k+2,y=0,width=1,height=1,period=6,phase=k%4))
    used_floor=set()
    for x,y in [(x,y) for y in range(h) for x in range(w)]+[p for p in decorative if not (0<=p[0]<w and 0<=p[1]<h)]:
        if not (0<=x<w and 0<=y<h):
            data=decorative[x,y]
        elif rows[y][x]=='#':
            mask=sum(v for dx,dy,v in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)] if 0<=x+dx<w and 0<=y+dy<h and rows[y+dy][x+dx]=='#')
            data=decorative.get((x,y),wall(mask,decoration.wall_kind(mask,x,y,number)))
        else:
            n=floor_selection.get((x,y),0)
            used_floor.add(n);data=f[n]
        for q in range(4):
            rr=by+y*2+(q//2);pos=rr*40+bx+x*2+(q%2);b=strips[bank(rr)]
            c=b.intern(data[q*8:q*8+8],f'cell{x},{y}/q{q}')
            if 0<=x<w and 0<=y<h:composition[(y*20+x)*4+q]=c
            assert 80<=pos<960,(x,y,pos)
            screen[pos-80]=c
            if (x,y) in decor_phase:
                kind,period,phase,variants=decor_phase[x,y]
                codes=[b.intern(v[q*8:q*8+8],kind+f'/phase{j}/q{q}') for j,v in enumerate(variants)]
                if len(set(codes))>1:
                    animations.append((pos,period,phase,codes))
                    animation_order.append((original_order.get(original_for_cell.get((x,y),(x,y)),y*w+x),q))
    #32 eight-byte records maximum, separate state per visual fragment.
    animations=[v for _,v in sorted(zip(animation_order,animations))]
    anim=background_animations+animations
    assert len(anim)<=32,(len(anim),'animation descriptors')
    desc=bytearray(544);desc[:8]=bytes([w,h,bx,by,len(anim),number,themes.AREA,1]);desc[536:541]=bytes(themes.SPEC['palette'])
    for i,b in enumerate(strips):
        desc[8+i*24:8+(i+1)*24]=bytes(v for t in objects[i] for v in t)
    for i,(pos,period,phase,codes) in enumerate(anim):
        struct.pack_into('<HBB4B',desc,128+i*8,0x8800+pos,period,phase&3,*codes)
    (OUT/f'scene-{number}-decoration.json').write_text(json.dumps(dict(variant=decoration.VARIANT,area=themes.AREA,anchors=floor_anchors,floor_selection=[dict(x=x,y=y,module=n) for (x,y),n in sorted(floor_selection.items())],devices=specs),indent=2)+'\n')
    report=[]
    rgb=json.loads(Path('assets/graphics/pal-palette.json').read_text())['rgb']
    for i,b in enumerate(strips):
        report.append(dict(bank=i,address=BANKS[i],absolute_rows=[2+i*4,5+i*4 if i<4 else 23],static_unique=len(b.data),dynamic_reserved=4,used=len(b.data)+4,free=124-len(b.data),references=b.refs,conflicts=b.conflicts))
        p=blank(64,64)
        for n,data in enumerate(b.pack()[k:k+8] for k in range(0,1024,8)):
            for yy,v in enumerate(data):
                for xx in range(4):p[n//16*8+yy][n%16*4+xx]=(v>>(6-2*xx))&3
        png(OUT/f'scene-{number}-bank-{i}.png',p,[rgb[v] for v in (0,238,156,132)])
    (OUT/f'scene-{number}-banks.json').write_text(json.dumps(dict(classification='CALCULATED compiled glyph allocation',banks=report,floor_modules=sorted(used_floor),devices=owners,animations=len(anim),geometry=[w,h,bx,by],conflicts=[]),indent=2)+'\n')
    sections=list(zip(BANKS,[b.pack() for b in strips]))+[(0x9800,bytes(screen)),(0x1400,bytes(composition)),(0xb160,cool(a['robot_frames'])),(0x9de0,bytes(desc))]
    return package('scene-'+str(number),sections,number+1)

def mono_image():
    # Authored code-native320x80 monochrome illustration: no resampling of art.
    p=blank(320,80)
    for x in (12,40,264,300):
        line(p,x,0,x,70,1);line(p,x+3,0,x+3,70,1)
    for y in (8,12):line(p,0,y,319,y,1)
    line(p,0,78,132,55,1);line(p,319,78,205,55,1)
    for x in (48,88,232):
        rect(p,x,22,32,34,1);rect(p,x+1,23,30,32,0)
        rect(p,x+5,28,22,12,1);rect(p,x+6,29,20,10,0)
        for y in (45,48):line(p,x+6,y,x+25,y,1)
        for xx in range(x+7,x+25,4):rect(p,xx,52,1,1,1)
    # Perspective service robot: continuous bright body, dark sensor visor,
    # lower tank treads, arm and forks; isolated silhouette in central space.
    for y in range(27,58):
        for x in range(139,193):
            if 4<=x-139<=49 and 2<=y-27<=28:p[y][x]=1
    rect(p,151,20,27,12,1);rect(p,154,23,21,5,0)
    rect(p,148,38,36,8,0);rect(p,151,40,7,3,1);rect(p,171,40,7,3,1)
    rect(p,135,55,23,12,1);rect(p,175,55,23,12,1)
    for y in (58,61,64):line(p,138,y,154,y,0);line(p,178,y,194,y,0)
    line(p,191,36,208,44,1);line(p,208,44,206,60,1)
    line(p,207,58,221,62,1);line(p,206,61,218,65,1)
    # Sparse dithering only on chassis flank; no noise behind typography.
    for y in range(49,54,2):
        for x in range(150,181,4):p[y][x]=0
    return bytes(sum(p[y][x+i]<<(7-i) for i in range(8)) for y in range(80) for x in range(0,320,8))

def menu(a):
    image=mono_image();font=json.loads(Path('assets/graphics/mono-font.json').read_text());charset=bytearray(1024)
    for i,c in enumerate(font['order'],1):charset[i*8:i*8+7]=bytes.fromhex(font['menu_rows_hex'][c])
    title=title_pixels();footer=footer_pixels()
    one=bytes(sum(row[x+i]<<(7-i) for i in range(8)) for row in title for x in range(0,320,8))
    two=bytes(sum(row[x+i*2]<<(6-2*i) for i in range(4)) for row in footer for x in range(0,320,8))
    assert len(one)==800 and len(two)==1200
    (OUT/'title-expected.json').write_text(json.dumps(title)+'\n')
    (OUT/'footer-expected.json').write_text(json.dumps(footer)+'\n')
    (OUT/'container-expected.json').write_text(json.dumps([container_pixels(),container_pixels(True)]+[container_pixels(True,i) for i in range(3)])+'\n')
    return package('menu',[(0xa000,image),(0xb000,one),(0x8c00,bytes(charset)),(0xb400,two)],4)

def music():
    # Original structured122.88s industrial synth piece,16 sections x64 rows.
    #3 independent channels; channel4 remains SFX. Eight distinct patterns.
    freq=[243,217,193,182,162,144,128,121,108,96,91,81,72,64,60,54,48,45,40,36,32,30,27,24]
    patterns=[]
    for part in range(8):
        chord=[0,5,3,7,0,8,5,7][part]
        melody=[12,15,19,15,14,17,21,17,12,14,15,19,17,15,14,10]
        for row in range(64):
            bass=freq[(chord+[0,0,7,0][row//16])%12+1]
            lead=freq[(melody[(row//4+part*3)%16]+(part//4)*2)%24] if part not in (0,4) or row%8<4 else 0
            drum=3 if row%16==8 else 1 if row%8==0 else 2 if row%4==2 else 0
            patterns.extend([bass,lead,drum])
    arrangement=[0,1,2,3,4,5,6,7,2,5,3,6,4,7,1,0]
    data=bytes(patterns+arrangement)
    (OUT/'music.json').write_text(json.dumps(dict(title='Service Current',origin='Original composition authored for NEON SHIFT 65 renderer qualification; no third-party samples',license='CC0-1.0',player='NS65 three-channel pattern/envelope tracker (candidate ASM, MIT)',pattern_count=8,rows_per_pattern=64,order=arrangement,row_frames=6,duration_seconds=16*64*6/50,data_bytes=len(data),channels='1 bass,2 lead/vibrato,3 drums,4 SFX'),indent=2)+'\n')
    return package('music',[(0x1800,data)],5)

def main():
    OUT.mkdir(parents=True,exist_ok=True);a=arrays();ll=levels()
    # Four independent ATRs already select their area through NEON_ART2_AREA.
    # Constants only: no extra runtime table, branch, byte or RAM allocation.
    pal=themes.SPEC['palette'];hud=0xe0 if themes.AREA==1 else pal[0]&0xf0
    loader=0x9c if themes.AREA==1 else pal[1]
    (OUT/'neon-palette.h').write_text(f'#define AREA_PF0 {pal[0]}\n#define AREA_PF3 {pal[3]}\n#define AREA_HUD {hud}\n')
    (OUT/'neon-palette.inc').write_text(f'AREA_LOADER = {loader}\n')

    (OUT/'levels.json').write_text(json.dumps(dict(levels=ll),indent=2)+'\n')
    results=[]
    for i,l in enumerate(ll):
        parse('\n'.join(l['rows']))
        path,states=solve_path('\n'.join(l['rows']))
        assert path is not None,(i,states)
        results.append(dict(scene=i,path=path,states=states))
    (OUT/'solutions.json').write_text(json.dumps(results,indent=2)+'\n')
    packs=[scene(l,i,a) for i,l in enumerate(ll)]+[menu(a),music()]
    import splash_assets
    packs.append(splash_assets.generate(sys.modules[__name__]))
    common=bytes(a['mono_font'])+bytes(a['menu_font'])
    # Resident common fonts are small and survive every partial read and BFS.
    code='#include "level.h"\n'
    for i,l in enumerate(ll):
        code+=f'static const char *rows{i}[]={{'+','.join(json.dumps(r) for r in l['rows'])+'};\n'
    code+='const Level prototype_levels[]={'+','.join('{rows'+str(i)+','+str(len(l['rows']))+','+json.dumps(l['name'])+'}' for i,l in enumerate(ll))+'};\n'
    code+='#ifdef __ATARI__\n#pragma rodata-name(push,"COMMON")\n#endif\n'
    code+='const unsigned char mono_font[]={'+','.join(map(str,a['mono_font']))+'};\n'
    code+='#ifdef __ATARI__\n#pragma rodata-name(pop)\n#endif\n'
    code+='const unsigned char menu_font[]={'+','.join(map(str,a['menu_font']))+'};\n'
    (OUT/'assets.c').write_text(code)
    digits=[]
    for c in '0123456789':
        data=a['mono_font'][(ord(c)-ord('0')+27)*8:][:8]
        for shift in range(8):
            digits.extend(v>>shift for v in data)
            digits.extend((v<<(8-shift))&255 if shift else 0 for v in data)
    assert len(digits)==1280
    (OUT/'numfont.s').write_text('.export hud_digits\n.segment "RODATA"\nhud_digits:\n'+''.join(' .byte '+','.join(map(str,digits[i:i+16]))+'\n' for i in range(0,len(digits),16)))
    (OUT/'prototype_assets.h').write_text('#include "level.h"\n#define PROTOTYPE_LEVEL_COUNT 3\nextern const Level prototype_levels[3];\nextern const unsigned char mono_font[352],menu_font[352];\n')
    (OUT/'packages.json').write_text(json.dumps(packs,indent=2)+'\n')
    # Actual C/ASM replay source; all undo steps checked against initial state.
    replay='#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n#include "game.h"\n#include "undo.h"\n#include "prototype_assets.h"\nstatic GameState g,original;\nint main(void){unsigned char p;unsigned int n;\n'
    for result in results:
        replay+='assert(game_start(&g,&prototype_levels['+str(result['scene'])+']));original=g;n=0;\n'
        for d in result['path']:
            dx,dy={'U':(0,-1),'D':(0,1),'L':(-1,0),'R':(1,0)}[d]
            replay+=f'assert(game_step(&g,{dx},{dy},&p));++n;\n'
        replay+='assert(level_is_solved(&g));while(n--)assert(undo_pop(&g));assert(!memcmp(&g,&original,sizeof(g)));\n'
    replay+='puts("PASS qualification solver paths in real C logic and full undo");return 0;}\n'
    (OUT/'replay.c').write_text(replay)
    print('PASS native strip compiler',[(p['name'],p['raw']) for p in packs])

import themes
themes.install(sys.modules[__name__])
import decoration
decoration.install(sys.modules[__name__])
if __name__=='__main__':main()
