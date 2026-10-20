"""Repack the HWVIS1 industrial illustration into simultaneous raster fonts.

Uses the existing four-area artwork and layout, not a replacement wall set.
Only offline art selection and exact glyph interning; no disk streaming in DMA.
"""
import json
import struct
import os
from pmg1_art import frames, tile, crate, dock
from warehouses import crc16

BANKS=(0x8c00,0xa000)
# Absolute character rows: HUD 0..1, fonts 2..12 / 13..23.
def bank(row):return 0 if row<13 else 1
def oldbank(row):return min((row-2)//4,4)

def sections(raw):
    return {a:raw[144+off:144+off+n] for a,n,off,_ in
            (struct.unpack_from('<4H',raw,16+8*i) for i in range(raw[6]))}

def package(parts):
    body=b''.join(b for _,b in parts);hdr=bytearray(144)
    hdr[:8]=b'NSRQ'+bytes([4,1,len(parts),0])
    struct.pack_into('<HH',hdr,8,len(body),crc16(body));off=0
    for i,(addr,b) in enumerate(parts):
        struct.pack_into('<4H',hdr,16+8*i,addr,len(b),off,crc16(b));off+=len(b)
    struct.pack_into('<H',hdr,12,crc16(hdr[16:]));struct.pack_into('<H',hdr,14,crc16(hdr[:14]))
    return bytes(hdr)+body

def bind_overlay(raw,code):
    assert len(code)==1024 and raw[4]==4
    return package([(a,code if a==0xa400 else b) for a,b in sections(raw).items()])

def install(c):
    energy=None
    if os.environ.get('NEON_ENERGY_DETAIL1')=='1':
        from energy_detail1_art import install as install_energy
        energy=install_energy(c)
    final=os.environ.get("NEON_ENERGY_FINAL1")=="1" and c.themes.AREA==1
    if final:
        from energy_final1_art import install as install_final
        energy=install_final(c)
    if final and os.environ.get('NEON_ENERGY_NEON1')=='1':
        from energy_neon1 import artwork
        artwork(energy)
    areas=os.environ.get('NEON_AREAS1')=='1'
    if areas:
        from neon_areas1_art import install as install_areas
        energy=install_areas(c,energy);final=True
    previous=c.scene
    old_devices=c.decoration.devices
    old_device=c.device
    old_background=c.decoration.background
    def devices(specs,number,level):
        selected=old_devices(specs,number,level)
        # Keep different large silhouettes per area, reduce repeated equipment.
        keep={1:(0,1,4),2:(0,2,5),3:(0,1,5),4:(1,2,4)}[c.themes.AREA]
        return [v for i,v in enumerate(selected) if i in keep]
    def device(kind,phase):
        # Fixed installation pose; small bright controls become area accents.
        return [[2 if v==1 else v for v in row] for row in old_device(kind,0)]
    def background(pos,data,animated):
        original=old_background(pos,data,animated)
        pixels=[[(v>>k)&3 for k in (6,4,2,0)] for v in original]
        # Drop stipple fields, preserve continuous drawing strokes and contours.
        transitions=sum(row[x]!=row[x+1] for row in pixels for x in range(3))
        filled=sum(v!=0 for row in pixels for v in row)
        if transitions>=16 and filled>=8:return bytes(8)
        return bytes(sum((3 if v else 0)<<(6-2*x) for x,v in enumerate(row)) for row in pixels)
    c.decoration.devices=devices;c.device=device;c.decoration.background=background
    c.decoration.floor_plan=lambda rows,number,specs:({},[])
    c.floors=lambda:[bytes(32)]*12

    def scene(level,number,arrays):
        previous(level,number,arrays)
        path=c.OUT/f'scene-{number}.nrq';old=sections(path.read_bytes())
        oldfonts=[old[a] for a in (0x8c00,0xa000,0xa400,0xa800,0xac00)]
        original_screen=old[0x9800];original_comp=old[0x1400]
        desc=bytearray(old[0x9de0]);bx,by=desc[2:4]
        vw,vh=level.get('visual_size',(16,8))
        background=energy.image(level) if energy else None
        # Preserve original reference origin and authored rectangle, including
        # the small-board composition with the equipment bank to its right.
        assert (bx,by)==(4,5)
        fonts=[[bytes(8)] for _ in BANKS];indices=[{bytes(8):0} for _ in BANKS]
        def intern(i,data,selector):
            if data not in indices[i]:
                n=len(fonts[i]);assert n<128,(level['number'],i,n+1,'industrial font overflow')
                indices[i][data]=n;fonts[i].append(data)
            return indices[i][data]|selector
        def trans(code,row):
            data=oldfonts[oldbank(row)][(code&127)*8:(code&127)*8+8]
            # Retain the gray reference drawing and the metal/area selectors.
            return intern(bank(row),data,code&128)
        objects=[tile(crate()),tile(crate(True)),tile(dock())]
        desc[8:128]=bytes(120)
        for i in range(2):
            for n,t in enumerate(objects+objects[1:2]*3):
                for q in range(4):desc[8+i*24+n*4+q]=intern(i,t[q*8:q*8+8],128)
        screen=bytearray(880);comp=bytearray(800)
        # Drawing outside puzzle includes wall-owned installation fragments.
        for pos,code in enumerate(original_screen,80):
            row,col=divmod(pos,40)
            if energy and not (by<=row<by+vh*2 and bx<=col<bx+vw*2):
                screen[pos-80]=intern(bank(row),energy.glyph(background,pos),energy.selector(level,row,col) if final else 128)
            else:
                screen[pos-80]=trans(code|128 if energy else code,row)
                if final:screen[pos-80]=(screen[pos-80]&127)|energy.selector(level,row,col)
        for y in range(8):
            for x in range(16):
                for q in range(4):
                    row=by+y*2+q//2
                    code=original_comp[(y*20+x)*4+q]
                    comp[(y*20+x)*4+q]=trans(code|128 if energy else code,row)
                    if final:comp[(y*20+x)*4+q]=(comp[(y*20+x)*4+q]&127)|energy.selector(level,row,bx+x*2+q%2)
                    if energy and (x>=vw or y>=vh):
                        pos=row*40+bx+x*2+q%2
                        comp[(y*20+x)*4+q]=intern(bank(row),energy.glyph(background,pos),energy.selector(level,row,bx+x*2+q%2) if final else 128)
        # Font feasibility measured on the exact final masks/objects, not on
        # compressed file sizes. Two raster banks are evaluated independently.
        three=[{bytes(8)},{bytes(8)},{bytes(8)}]
        for row in range(2,24):
            i=0 if row<8 else 1 if row<16 else 2
            for col in range(40):
                code=screen[(row-2)*40+col]
                three[i].add(fonts[bank(row)][code&127])
        for i in range(3):
            for t in objects:
                three[i].update(t[q:q+8] for q in range(0,32,8))
        desc[4]=0;desc[128:536]=bytes(408)
        desc[536:541]=bytes([238,{1:0xe8,2:0xb8,3:0x48,4:0x38}[c.themes.AREA],2,6,0])
        if energy:desc[536]=0xee if final else 0x28
        desc[541:544]=bytes([vw,vh,4])
        ambient=[]
        if final and os.environ.get('NEON_ENERGY_FIX1')=='1':
            if areas:
                from neon_areas1_art import descriptors
            else:
                from energy_fix1_ambient import descriptors
            entries,ambient=descriptors(energy,level,fonts,screen)
            desc[4]=len(ambient);desc[128:128+len(entries)]=entries
        if areas:
            from neon_areas1_art import neon_data
            desc[160:258]=neon_data(c.themes.AREA)
        parts=[(a,b''.join(f)+bytes(1024-len(f)*8)) for a,f in zip(BANKS,fonts)]
        parts += [(0xa400,bytes(1024)),(0x9800,bytes(screen)),(0x1400,bytes(comp)),(0xb160,frames()),(0x9de0,bytes(desc))]
        raw=package(parts);assert len(raw)==6080
        path.write_bytes(raw)
        (c.OUT/f'scene-{number}-industrial.json').write_text(json.dumps(dict(
            level=level.get('number'),area=c.themes.AREA,visual=[vw,vh],origin=[bx,by],
            fonts=[dict(address=a,rows=[2,12] if i==0 else [13,23],glyphs=len(f),free=128-len(f)) for i,(a,f) in enumerate(zip(BANKS,fonts))],
            three_fonts_glyphs=[len(s) for s in three],three_fonts_fit=all(len(s)<=128 for s in three),
            devices=json.loads((c.OUT/f'scene-{number}-decoration.json').read_text())['devices'],
            environment_animations=len(ambient),ambient=ambient,reference='ENERGY-FINAL1 metal panels and service accents; original PMG1 objects' if final else 'ENERGY-DETAIL1 offline panels/equipment; original puzzle geometry and PMG1 objects' if energy else 'HWVIS1 compiler, same wall masks/layout; reduced equipment and stipple',
            palette=list(desc[536:541])),indent=2)+'\n')
        return dict(name=f'scene-{number}',kind=number+1,bytes=len(raw),raw=len(raw)-144,sections=[dict(address=a,size=len(b)) for a,b in parts])
    c.scene=scene
