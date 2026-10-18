#!/usr/bin/env python3
"""Read-only native raster oracle for the candidate's real display lists."""
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from m1_check import png

def labels(path):return {n:int(h,16) for h,n in re.findall(r'^al (\w+) \.(\w+)',Path(path).read_text(),re.M)}
def state(path,l):
    b=Path(path).read_bytes();g=l['_gs']
    return dict(phase=b[l['_phase']],scene=b[l['_scene']],error=b[l['_error']],loaded=b[l['_loaded']],
        player=list(b[g+762:g+764]),boxes=[list(b[g+764+i*2:g+766+i*2]) for i in range(b[g+784])],
        moves=int.from_bytes(b[g+785:g+789],'little'),pushes=int.from_bytes(b[g+789:g+793],'little'),
        undo=int.from_bytes(b[l['_count']:l['_count']+2],'little'),overflow=b[l['_input_overflows']],
        publication_overflow=b[l['_publication_overflow']],late=b[l['_publish_late']],vcount=b[l['_publication_vcount']])

def pixel_reference(out,frame,l):
    out=Path(out);ram=(out/f'raster-{frame:04}.ram').read_bytes();im,pal=png(out/f'native-{frame:04}.png')
    previous=out/f'raster-{frame-1:04}.ram'
    reactivating=bool(previous.exists() and not previous.read_bytes()[l['_display_active']] and ram[l['_display_active']])
    blank=all(pal[im[y][x]]==pal[ram[0x2c8]] for y in range(24,216) for x in range(8,328))
    if not ram[l['_display_active']] and not ram[0x022f]:
        assert blank,(frame,'native DMA-off screen is not completely blank')
        return dict(frame=frame,pixels=320*192,status='PASS',mode='MEASURED complete DMA-off blank during resident screen preparation')
    if reactivating and blank:
        return dict(frame=frame,pixels=320*192,status='PASS',mode='MEASURED one complete blank on ANTIC reactivation after previous raster DMA-off; next active frame must pass normal oracle')
    colors=[ram[0x2c8]]+[ram[0x2c4+i] for i in range(4)]
    colors[2]=ram[l['_display_pf1']];colors[3]=ram[l['_display_pf2']]
    bank=ram[l['_display_font']]*256;dl=0x9f60;y=0;address=0;dli=0;diff=[];points=0
    while True:
        op=ram[dl];dl+=1;mode=op&15
        if mode==1:break
        if mode==0:
            height=((op>>4)&7)+1
            for yy in range(height):
                if y+yy>=24:
                    for x in range(320):
                        if pal[im[y+yy][8+x]]!=pal[colors[0]]:diff.append((x,y+yy,'blank'))
            y+=height;continue
        assert mode in (2,4,14,15),(frame,hex(dl),mode)
        if op&64:address=int.from_bytes(ram[dl:dl+2],'little');dl+=2
        height=1 if mode in (14,15) else 8
        for yy in range(height):
            for x in range(320):
                if mode==14:
                    value=ram[address+x//8];p=(value>>(6-2*((x%8)//2)))&3;color=colors[p]
                elif mode==15:
                    value=ram[address+x//8];bit=(value>>(7-x%8))&1
                    color=(colors[3]&240)|(colors[2]&15) if bit else colors[3]
                else:
                    code=ram[address+x//8];value=ram[bank+(code&127)*8+yy]
                    if mode==2:
                        bit=((value>>(7-x%8))&1)^bool(code&128)
                        color=(colors[3]&240)|(colors[2]&15) if bit else colors[3]
                    else:
                        p=(value>>(6-2*((x%8)//2)))&3;color=colors[4 if p==3 and code&128 else p]
                if pal[im[y+yy][8+x]]!=pal[color]:diff.append((x,y+yy,mode))
                points+=1
        address+=40;y+=height
        if op&128:
            bank=ram[l['_dli_font']+dli]*256;colors[2]=ram[l['_dli_pf1']+dli];colors[3]=ram[l['_dli_pf2']+dli];dli+=1
    assert y==216,(frame,y)
    assert not diff,(frame,len(diff),diff[:8])
    return dict(frame=frame,pixels=points,dlis=dli,status='PASS')

def pixel(out,frame,l):
    from pixel_fast import pixel as fast
    return fast(out,frame,l)

def check(out,frames):
    out=Path(out);l=labels(out/'candidate.lbl');states=[];pixels=[]
    for f in frames:
        s=state(out/f'frame-{f:04}.ram',l);s['frame']=f
        assert s['overflow']==s['publication_overflow']==s['late']==0,(f,s)
        states.append(s)
        raster=(out/f'raster-{f:04}.ram').read_bytes();end=(out/f'frame-{f:04}.ram').read_bytes()
        if raster[l['_asset_loading']] or end[l['_asset_loading']]:
            pixels.append(dict(frame=f,status='LOADING',reason='DMA disabled during actual SIO/validation; transition raster excluded'))
        else:pixels.append(pixel(out,f,l))
    r=dict(status='PASS',states=states,pixels=pixels,timing=json.loads((out/'timing.json').read_text()))
    assert r['timing']['csp_outside_samples']==0
    (out/'checked.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS native pixel oracle',len(frames),'frames')
    return r

if __name__=='__main__':
    out=Path(sys.argv[1]);frames=[int(n) for n in sys.argv[2:]];check(out,frames)
