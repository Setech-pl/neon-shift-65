#!/usr/bin/env python3
"""Verify read-only native device-playback evidence; nonzero on any mismatch."""
import csv,hashlib,json,re,struct,zlib
from pathlib import Path
ROOT=Path('build');levels=json.loads(Path('assets/levels/prototypes.json').read_text())['levels']
def png(path):
    b=path.read_bytes();pos=8;compressed=b'';palette=None
    while pos<len(b):
        n=int.from_bytes(b[pos:pos+4],'big');tag=b[pos+4:pos+8];data=b[pos+8:pos+8+n];pos+=n+12
        if tag==b'IHDR':w,h,depth,kind,_,_,_=struct.unpack('>IIBBBBB',data);assert depth==8 and kind==3
        if tag==b'PLTE':palette=[list(data[i:i+3]) for i in range(0,len(data),3)]
        if tag==b'IDAT':compressed+=data
    raw=zlib.decompress(compressed);rows=[];prev=[0]*w;p=0
    for y in range(h):
        mode=raw[p];p+=1;row=list(raw[p:p+w]);p+=w
        for x in range(w):
            a=row[x-1] if x else 0;c=prev[x-1] if x else 0;up=prev[x]
            if mode==1:v=a
            elif mode==2:v=up
            elif mode==3:v=(a+up)//2
            elif mode==4:
                q=a+up-c;ds=[abs(q-a),abs(q-up),abs(q-c)];v=[a,up,c][ds.index(min(ds))]
            else:assert mode==0;v=0
            row[x]=(row[x]+v)&255
        rows.append(row);prev=row
    return rows,palette

def check(name,expected,pixel_frames=(),source_levels=levels):
    out=ROOT/name
    labels={m.group(2):int(m.group(1),16) for m in re.finditer(r'^al ([0-9A-Fa-f]+) \.([\w]+)',(out/'candidate.lbl').read_text(),re.M)}
    artifact=json.loads((out/'artifact.json').read_text());assert artifact['sha256']==hashlib.sha256((out/'candidate.xex').read_bytes()).hexdigest()
    results=[]
    for p in [out/f'frame-{f:04}.ram' for f in artifact.get('captures',sorted(int(p.stem[-4:]) for p in out.glob('frame-*.ram')))]:
        b=p.read_bytes();g=labels['_gs'];f=labels['_flow'];u=lambda a,n=2:int.from_bytes(b[a:a+n],'little');frame=int(p.stem[-4:]);scene=b[f+2]
        r=dict(frame=frame,phase=b[f],scene=scene,player=list(b[g+762:g+764]),moves=u(g+785,4),pushes=u(g+789,4),overflow=b[labels['_input_overflows']],full=u(labels['_render_full_boards']),undo=u(labels['_count']),tiles=u(labels['_render_tile_writes']))
        assert r['overflow']==0,(name,r)
        if frame in expected:
            wanted=expected[frame];assert [r[k] for k in ['phase','scene','player','moves','pushes','undo']]==wanted,(name,r,wanted)
        if r['full'] and r['phase'] in [1,2,3,4,5]:
            rows=source_levels[scene]['rows'];static=bytearray(b'#'*760)
            for y,row in enumerate(rows):
                for x,c in enumerate(row):static[y*38+x]=ord('#' if c=='#' else '.' if c in '.*+' else ' ')
            assert b[g:g+760]==static,(name,frame,'native map tiles')
        if frame in pixel_frames and r['phase'] in (1,2,3,4):
            index=b[labels['_robot_frame']]
            if index<40:
                address=labels['_robot_frames']+index*32
                assert b[0x8ec0:0x8ee0]==b[address:address+32],(name,frame,'stale robot glyph',index)
        if frame in pixel_frames:
            raster=(out/f'raster-{frame:04}.ram').read_bytes()
            image,palette=png(out/f'native-{frame:04}.png');v=json.loads((out/f'video-{frame:04}.json').read_text());assert v['dma']==34
            colors=[raster[0x2c8]]+[raster[0x2c4+i] for i in range(4)]
            colors[2]=raster[labels['_display_pf1']];colors[3]=raster[labels['_display_pf2']]
            bank=raster[labels['_display_font']]*256
            mismatches=0;dl=0x8bc3;address=0x8800;dli=0
            for row in range(24):
                instruction=raster[dl];dl+=1;mode=instruction&15
                assert mode in (2,4),(name,frame,row,mode)
                if instruction&64:
                    address=int.from_bytes(raster[dl:dl+2],'little');dl+=2
                assert address==0x8800+row*40,(name,frame,row,'LMS drift')
                for gy in range(8):
                    for x in range(320):
                        code=raster[address+x//8];glyph=raster[bank+(code&127)*8+gy]
                        if mode==2:
                            bit=((glyph>>(7-x%8))&1)^bool(code&128)
                            color=(colors[3]&240)|(colors[2]&15) if bit else colors[3]
                        else:
                            pixel=(glyph>>(6-2*((x%8)//2)))&3
                            color=colors[4 if pixel==3 and code&128 else pixel]
                        if palette[image[24+row*8+gy][8+x]]!=palette[color]:mismatches+=1
                address+=40
                if instruction&128:
                    assert dli<6,(name,frame,'too many DLIs')
                    bank=raster[labels['_dli_font']+dli]*256
                    colors[2]=raster[labels['_dli_pf1']+dli];colors[3]=raster[labels['_dli_pf2']+dli];dli+=1
            assert raster[dl:dl+3]==bytes([0x41,0xc0,0x8b]),(name,frame,'JVB drift')
            assert mismatches==0,(name,frame,'native PNG != hardware bytes',mismatches)
            r['native_pixel_oracle']='PASS 61440 physical pixels'
        results.append(r)
    timing=json.loads((out/'timing.json').read_text());assert timing['csp_outside_samples']==0
    events=list(csv.DictReader((out/'events.csv').open()));durations=[]
    for i,a in enumerate(events):
        if a['event']=='begin' and i+4<len(events) and events[i+4]['event']=='end':durations.append(dict(frame=int(a['frame']),cycles=int(events[i+4]['clock'])-int(a['clock'])))
    report=dict(status='PASS',artifact=artifact,states=results,stack=timing,slowest_iterations=sorted(durations,key=lambda a:a['cycles'],reverse=True)[:18],timing_note='ANTIC CPU_CLOCK includes DMA and interrupts; transitions may span frames; not exclusive CPU cycles or a whole-product worst case')
    (out/'checked.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',name,'captures',len(results),'native pixel frames',list(pixel_frames));return report

if __name__=='__main__':
    reports=[]
    reports.append(check('m1-controls',{200:[1,0,[5,4],0,0,0],241:[1,0,[6,4],1,0,1],351:[1,0,[7,2],6,1,6],371:[1,0,[6,2],5,0,5],391:[1,0,[5,2],4,0,4],411:[3,0,[5,2],4,0,4],471:[4,0,[5,2],4,0,4],491:[1,0,[5,2],4,0,4],600:[1,0,[5,4],0,0,0]},[120,200,351,411,600]))
    reports.append(check('m1-foundry',{340:[2,1,[5,8],5,1,5],360:[1,1,[6,8],4,0,4],380:[2,1,[5,8],5,1,5],420:[1,2,[3,1],0,0,0],460:[2,2,[2,1],1,1,1],490:[2,2,[2,1],1,1,1],520:[5,2,[2,1],1,1,1]},[90,340,380,420,490,520]))
    for cap in [256,128,64]:reports.append(check('m1-ring-'+str(cap),{2140:[1,1,[4,8],600,0,cap],3090:[1,1,[4,8],600-cap,0,0]},[330,3090]))
    (ROOT/'m1-native-report.json').write_text(json.dumps(dict(status='PASS',runs=reports),indent=2)+'\n')
