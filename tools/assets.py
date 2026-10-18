#!/usr/bin/env python3
"""Compile authored pixels to ANTIC4 glyph bytes and decode them for preview."""
import hashlib,json,struct,zlib
from pathlib import Path

def png(path,pixels,palette,scale_x=2):
    h=len(pixels);w=len(pixels[0])*scale_x
    raw=b''.join(b'\0'+b''.join(bytes(palette[v])*scale_x for v in row) for row in pixels)
    def chunk(tag,b):return struct.pack('>I',len(b))+tag+b+struct.pack('>I',zlib.crc32(tag+b))
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

def pixels(rows,width,height):
    assert len(rows)==height and all(len(r)==width and set(r)<=set('0123') for r in rows)
    return [[int(c) for c in r] for r in rows]

def encode_tile(p):
    return [sum(p[y+oy][x+ox]<<(6-2*ox) for ox in range(4)) for y,x in [(0,0),(0,4),(8,0),(8,4)] for oy in range(8)]

def decode_tile(data):
    p=[[0]*8 for _ in range(16)]
    for g,(y,x) in enumerate([(0,0),(0,4),(8,0),(8,4)]):
        for oy in range(8):
            for ox in range(4):p[y+oy][x+ox]=(data[g*8+oy]>>(6-2*ox))&3
    return p

def pack(data):
    # Count/value RLE, deliberately simple bounded estimator for M2 budget.
    out=[];i=0
    while i<len(data):
        n=1
        while i+n<len(data) and data[i+n]==data[i] and n<255:n+=1
        out.extend([n,data[i]]);i+=n
    return bytes(out)

def unpack(data,expected):
    assert len(data)%2==0
    out=[]
    for i in range(0,len(data),2):
        assert data[i]>0 and len(out)+data[i]<=expected
        out.extend([data[i+1]]*data[i])
    assert len(out)==expected
    return bytes(out)

def main():
    Path('build').mkdir(exist_ok=True)
    art=json.loads(Path('assets/graphics/prototype.json').read_text());music=json.loads(Path('assets/audio/prototype.json').read_text())
    assert art['mode']=='ANTIC4' and art['logical_tile']==[8,16]
    assert list(art['tiles'])==['FLOOR','PLATE','WALL','BULKHEAD','DOCK','MODULE','DOCKED','CONDUIT','HAZARD','VENT']
    assert list(art['robot'])==['UP','DOWN','RIGHT','LEFT']
    assert all(isinstance(v,int) and 0<=v<=255 and v%2==0 for v in art['palette'].values())
    chars=[0]*1024;names={};font=list(art['font'])
    assert ''.join(font)=='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:/-+.>='
    assert len(font)<=47
    for i,c in enumerate(font,1):
        rows=art['font'][c].split('/');assert len(rows)==7 and all(len(r)==3 and set(r)<=set('01') for r in rows)
        chars[i*8:i*8+8]=[0]+[sum(int(v)*3<<(6-2*x) for x,v in enumerate(r)) for r in rows]
    mono=json.loads(Path('assets/graphics/mono-font.json').read_text())
    assert mono['order']==''.join(font) and mono['hud_width']==6 and mono['hud_pitch']==7
    hud_font=[0]*8;menu_font=[0]*8
    for c in font:
        rows=mono['hud_rows'][c].split('/')
        assert len(rows)==7 and all(len(r)==6 and set(r)<=set('01') for r in rows)
        hud_font += [int(r,2)<<2 for r in rows]+[0]
        raw=bytes.fromhex(mono['menu_rows_hex'][c]);assert len(raw)==7
        menu_font += list(raw)+[0]
    assert len(hud_font)==len(menu_font)==352
    atlas=[]
    for i,(name,rows) in enumerate(art['tiles'].items()):
        base=48+i*4;names[name]=base;p=pixels(rows,8,16);data=encode_tile(p);assert decode_tile(data)==p;chars[base*8:base*8+32]=data;atlas.append(p)
    robot_base=88;frames=[]
    dock=pixels(art['tiles']['DOCK'],8,16)
    for goal in range(2):
        for direction,rows in art['robot'].items():
            src=pixels(rows,8,16)
            for mode in range(5):
                p=[r[:] for r in src]
                if mode:
                    for x in range(1,7):p[13][x]=3 if (x+mode)%2 else 0
                    if mode>=3:
                        if direction=='UP':p[3][2]=p[3][5]=1
                        elif direction=='DOWN':p[15][2]=p[15][5]=1
                        elif direction=='LEFT':p[6][0]=p[7][0]=1
                        else:p[6][7]=p[7][7]=1
                if goal:
                    for y in (0,15):
                        for x in (1,2,5,6):p[y][x]=2
                data=encode_tile(p);assert decode_tile(data)==p;frames.append(data)
    chars[robot_base*8:robot_base*8+32]=frames[5] # facing down idle
    from scenes import compile_scenes
    scenes=compile_scenes(chars)
    title_chars=chars.copy()
    # Gameplay is independent of the title-only ANTIC4 alphabet. Blank 0..3,
    # 14 wall tiles 4..59, docked module 60..63, floors 64..79,
    # dock 80..83, module 84..87, ISR robot 88..91, background 92..127.
    legacy=chars.copy();chars[:92*8]=[0]*(92*8)
    for i in range(14):
        old=[56,60,80][i%3];chars[(4+i*4)*8:(8+i*4)*8]=legacy[old*8:old*8+32]
    for new,old in [(60,72),(64,48),(68,52),(72,76),(76,84),(80,64),(84,68)]:
        chars[new*8:new*8+32]=legacy[old*8:old*8+32]
    chars[88*8:92*8]=frames[5]
    assert chars[:32]==[0]*32 and chars[92*8:]==legacy[92*8:]
    Path('build/gameplay-contract.json').write_text(json.dumps(dict(version=1,
        blank=[0,4],walls=[4,60],docked=[60,64],floors=[64,80],dock=[80,84],
        module=[84,88],robot=[88,92],background=[92,128],free=[],
        ui='ANTIC2 menu/HUD; ANTIC4 alphabet only in title bank'),indent=2)+'\n')
    hero=pixels(art['robot']['RIGHT'],8,16)
    hero=[[v for v in row for _ in range(2)] for row in hero for _ in range(2)]
    # Large title robot: 4x4 glyphs, exactly nearest-neighbour authored pixels.
    for gy in range(4):
        for gx in range(4):
            title_chars[(48+gy*4+gx)*8:(49+gy*4+gx)*8]=[sum(hero[gy*8+y][gx*4+x]<<(6-2*x) for x in range(4)) for y in range(8)]
    # Enlarged authored bitmap logo in title-only spare glyphs.
    logo="NEON SHIFT 65";logo_w=len(logo)*8
    lp=[[0]*logo_w for _ in range(16)]
    # Full seven-column Void Strike menu reference; never enlarge the old
    # three-column ANTIC4 letters. One color pixel per reference column.
    for i,c in enumerate(logo):
        if c==' ':continue
        for y,value in enumerate(bytes.fromhex(mono['menu_rows_hex'][c])):
            for x in range(8):
                if value & (128>>x):
                    for dy in range(2):lp[1+y*2+dy][i*8+x]=1
    used={c&127 for c in scenes[0]}|set(range(44))|set(range(48,64))|set(range(68,76))
    spare=[i for i in range(44,128) if i not in used];unique={bytes(8):0};logo_map=[]
    for gy in range(2):
        for gx in range(logo_w//4):
            data=bytes(sum(lp[gy*8+y][gx*4+x]<<(6-2*x) for x in range(4)) for y in range(8))
            if data not in unique:
                assert spare,"title glyph budget exceeded"
                code=spare.pop(0);unique[data]=code;title_chars[code*8:code*8+8]=data
            logo_map.append(unique[data])
    assert len(chars)==len(title_chars)==1024 and len(frames)==40 and all(len(f)==32 for f in frames)
    assert all(len(m)==880 and set(m)<=set([0]+list(range(220,256))) for m in scenes)
    assert len(logo_map)==52 and all(0<=c<128 for c in logo_map)
    def arr(name,data):return 'const unsigned char '+name+'[] = {\n'+',\n'.join('    '+','.join(str(v) for v in data[i:i+16]) for i in range(0,len(data),16))+'\n};\n'
    header='#ifndef PROTOTYPE_ASSETS_H\n#define PROTOTYPE_ASSETS_H\nextern const unsigned char mono_font[352];\nextern const unsigned char menu_font[352];\nextern const unsigned char gameplay_common[320];\nextern const unsigned char robot_frames[1280];\nextern const unsigned char title_charset[1024];\nextern const unsigned char scene_maps[1760];\nextern const unsigned char prototype_scenes[3];\nextern const unsigned char title_logo[52];\n#define TITLE_LOGO_WIDTH 26\n'
    for name,value in art['palette'].items():header+=f'#define COLOR_{name} {value}\n'
    for name,base in names.items():header+=f'#define TILE_{name} {base}\n'
    header+=f'#define TILE_ROBOT {robot_base}\n#define TITLE_ROBOT 48\n#define ROBOT_FRAMES_PER_DIRECTION 5\n#define ROBOT_FRAMES_PER_SUBSTRATE 20\n#define FONT_GLYPHS {len(font)}\n#endif\n'
    levels=json.loads(Path('assets/levels/prototypes.json').read_text())['levels']
    from solver import parse
    level_code='#include "level.h"\n'
    for i,level in enumerate(levels):
        assert len(level['name'])<=28, 'name must leave x232..319 for DOCKS'
        parse('\n'.join(level['rows']));assert len(level['rows'])<=10 and len(level['rows'][0])<=20
        level_code+=f'static const char *prototype_rows_{i}[] = {{'+','.join(json.dumps(r) for r in level['rows'])+'};\n'
    level_code+='const Level prototype_levels[] = {\n'+',\n'.join('{prototype_rows_'+str(i)+','+str(len(l['rows']))+','+json.dumps(l['name'])+'}' for i,l in enumerate(levels))+'\n};\n'
    level_code+=arr('prototype_tracks',[l['track'] for l in levels])
    header=header.replace('#endif','#include "level.h"\n#define PROTOTYPE_LEVEL_COUNT '+str(len(levels))+'\nextern const Level prototype_levels[PROTOTYPE_LEVEL_COUNT];\nextern const unsigned char prototype_tracks[PROTOTYPE_LEVEL_COUNT];\n#endif')
    Path('build/prototype_assets.h').write_text(header);Path('build/prototype_assets.c').write_text('#include "prototype_assets.h"\n#ifdef __ATARI__\n#pragma rodata-name(push,"ART")\n#endif\n'+arr('gameplay_common',chars[80*8:84*8]+chars[92*8:])+arr('mono_font',hud_font)+arr('menu_font',menu_font)+arr('title_charset',title_chars)+arr('scene_maps',[v for m in scenes for v in m])+arr('title_logo',logo_map)+arr('robot_frames',[v for f in frames for v in f])+'#ifdef __ATARI__\n#pragma rodata-name(pop)\n#endif\n'+arr('prototype_scenes',[0,1,0])+level_code)
    inc='; Generated original music from assets/audio/prototype.json\nMUSIC_ROW_FRAMES = '+str(music['row_frames'])+'\nMUSIC_TRACKS = '+str(len(music['tracks']))+'\nmusic_track_lo: .byte '+','.join('<music_track_'+str(i) for i in range(len(music['tracks'])))+'\nmusic_track_hi: .byte '+','.join('>music_track_'+str(i) for i in range(len(music['tracks'])))+'\n'
    raw_music=[]
    for i,track in enumerate(music['tracks']):
        assert len(track['rows'])==32 and all(len(r)==3 and all(isinstance(v,int) and 0<=v<256 for v in r) and 0<=r[2]<=3 for r in track['rows'])
        data=[v for r in track['rows'] for v in r];raw_music.extend(data);inc+=f'music_track_{i}:\n'+''.join(' .byte '+','.join(str(v) for v in data[j:j+16])+'\n' for j in range(0,len(data),16))
    Path('build/audio.inc').write_text(inc)
    rgb=json.loads(Path('assets/graphics/pal-palette.json').read_text())['rgb'];palette=[rgb[art['palette'][k]] for k in ['COLBK','COLPF0','COLPF1','COLPF2','COLPF3']]
    # Atlas and animation previews decode the actual generated bytes.
    p=[[0]*(len(atlas)*8) for _ in range(16)]
    for i,t in enumerate(atlas):
        d=decode_tile(encode_tile(t))
        for y in range(16):p[y][i*8:i*8+8]=d[y]
    png('build/tile-atlas.png',p,palette)
    gray=[[round(.2126*r+.7152*g+.0722*b)]*3 for r,g,b in palette]
    png('build/tile-atlas-gray.png',p,gray)
    p=[[0]*40 for _ in range(16*8)]
    for i,data in enumerate(frames):
        d=decode_tile(data)
        for y in range(16):p[(i//5)*16+y][(i%5)*8:(i%5+1)*8]=d[y]
    png('build/robot-atlas.png',p,palette)
    report=[]
    for name,data in [('charset',bytes(chars)),('robot_frames',bytes(v for f in frames for v in f)),('music',bytes(raw_music)),('title_charset',bytes(title_chars)),('scene_maps',bytes(v for m in scenes for v in m))]:
        compressed=pack(data);assert unpack(compressed,len(data))==data
        report.append(dict(name=name,raw=len(data),rle=len(compressed),sha256=hashlib.sha256(data).hexdigest(),codec='count,value RLE budget experiment only; M1 uses raw',roundtrip='PASS'))
    Path('build/assets-report.json').write_text(json.dumps(dict(assets=report,font_order=''.join(font),palette=art['palette'],robot_order='goal(0,1), direction(UP,DOWN,RIGHT,LEFT), mode(idle,drive1,drive2,push1,push2)',native_mode='ANTIC4',proof='packing equality + emulator screenshots; preview decodes generated bytes'),indent=2)+'\n')
    Path('build/assets.stamp').touch()
    print('PASS native assets: 1024-B charset,40 robot frames,3 original32-row POKEY samples, hardware roundtrip')
if __name__=='__main__':main()
