#!/usr/bin/env python3
"""Finite actual ATR tests. Read-only PAL observer; no injected game RAM.

Requires Pillow/numpy and a separately built Atari800 NS65 observer + legal ROM
config. Records are sparse; movies use 320 consecutive rasters per area.
"""
import argparse,csv,gzip,hashlib,json,os,re,shutil,struct,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from atmosphere1_owner_smoke import prepare,save_span
from pmg_industrial1_art import sections
from warehouses import crc16
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/atmosphere1'
DOC=ROOT/'docs/atmosphere1'
LEVELS=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
STICK=dict(U=14,D=13,L=11,R=7)

def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def labels(p):return {n:int(h,16) for h,n in re.findall(r'^al (\w+) \.(\w+)',p.read_text(),re.M)}
def state(b,l):
    g=l['_gs']
    s={k:b[l['_'+k]] for k in ('phase','scene','error','loaded','asset_loading','pmg_active','music_enabled','sfx_enabled','save_error')}
    s.update(player=list(b[g+762:g+764]),boxes=[list(b[g+764+i*2:g+766+i*2]) for i in range(b[g+784])],moves=int.from_bytes(b[g+785:g+789],'little'),pushes=int.from_bytes(b[g+789:g+793],'little'),undo=int.from_bytes(b[l['_count']:l['_count']+2],'little'))
    for k in ('_input_overflows','_publication_overflow','_publish_late'):assert b[l[k]]==0,(k,s)
    return s

def sec(disk,i):
    at=16+(1100+i*70)*128
    return sections(disk[at:at+6080])

def save_image(disk,n,record=None):
    """Valid on-disk NSAV fixture; Continue executes all normal loader paths."""
    d=bytearray(disk);at=16+(1099+(n-1)*70)*128;board=d[at:at+128]
    lev=LEVELS[n-1]
    p=next([x,y] for y,row in enumerate(lev['rows']) for x,c in enumerate(row) if c in '@+')
    boxes=[[x,y] for y,row in enumerate(lev['rows']) for x,c in enumerate(row) if c in '$*']
    moves=pushes=0
    if record:p,boxes,moves,pushes=record['player'],record['boxes'],record['moves'],record['pushes']
    r=bytearray(128);r[:10]=b'NSAV'+bytes((1,n-1,3,0,1,0));r[10:14]=board[12:16];r[14:16]=board[126:128]
    r[16:19]=bytes(p+[len(boxes)]);r[19:19+2*len(boxes)]=bytes(v for b in boxes for v in b)
    r[39:43]=moves.to_bytes(4,'little');r[43:47]=pushes.to_bytes(4,'little');r[126:]=crc16(r[:126]).to_bytes(2,'little')
    d[save_span(d)]=r+bytes(128)
    return d

def pixel(out,f,l,disk):
    b=(out/f'raster-{f:04}.ram').read_bytes();rr=np.frombuffer(b,dtype=np.uint8)
    if not b[l['_display_active']] or b[l['_asset_loading']] or b[l['_phase']] not in (1,2):return False
    im=Image.open(out/f'native-{f:04}.png');pal=np.array(im.getpalette(),dtype=np.uint8).reshape(-1,3);im=np.array(im)
    want=np.zeros((240,336),dtype=np.uint8);colors=[0,*b[0x2c4:0x2c8]]
    for row in range(2,24):
        codes=rr[0x8800+row*40:0x8800+(row+1)*40];a=0x8c00 if row<13 else 0xa000
        v=rr[a+(codes.astype(np.uint16)&127)[:,None]*8+np.arange(8)].T
        pp=(v[:,:,None]>>np.array([6,4,2,0]))&3
        ci=np.where((pp==3)&((codes[None,:,None]&128)!=0),4,pp)
        want[24+row*8:32+row*8,8:328]=np.repeat(np.array(colors)[ci].reshape(8,160),2,axis=1)
    if b[l['_pmg_active']]:
        x,y=b[l['_pmg_visible_x']],b[l['_pmg_visible_y']]
        for yy in range(16):
            for xx in range(8):
                color=238 if b[0xac00+y+yy]&(128>>xx) else 158 if b[0xad00+y+yy]&(128>>xx) else None
                if color is not None:want[y-8+yy,8+2*(x-48+xx):10+2*(x-48+xx)]=color
    for yy in range(32):
        for xx in range(8):
            color=b[0x2c2] if b[0xae68+yy]&(128>>xx) else b[0x2c3] if b[0xaf68+yy]&(128>>xx) else None
            if color is not None:want[96+yy,16+2*xx:18+2*xx]=color
    x=b[l['cable_head']];want[49:51,8+2*(x-48):12+2*(x-48)]=b[0x2c2]
    diff=np.any(pal[im[40:216,8:328]]!=pal[want[40:216,8:328]],axis=2)
    assert not diff.any(),(out.name,f,int(diff.sum()),'raster')
    parts=sec(disk,b[l['_scene']])
    for a in (0x8c00,0xa000):assert b[a:a+1024]==parts[a],(f,'immutable font')
    return True

def probe(name,mode,events,frames,total,image=None,audio=False,baseline=False,rec=None,realtime=False):
    out=BASE/'runs'/name
    b=ROOT/'build/atmosphere1-baseline' if baseline else BASE/('normal-r2' if mode=='normal' else 'test-'+mode+'-r2')
    l=labels(b/'candidate.lbl')
    master=b/'candidate.atr'
    master_digest=sha(master)
    if (out/'summary.json').exists():
        j=json.loads((out/'summary.json').read_text())
        assert j['master_sha256']==master_digest and j['events']==json.loads(json.dumps(events)) and j['frames']==frames
        return out,{int(k):v for k,v in j['states'].items()},l
    out.mkdir(parents=True,exist_ok=False)
    if rec:play=Path(rec['opened_atr'])
    else:
        play=out/'play.atr';play.write_bytes(image if image is not None else master.read_bytes())
    initial=play.read_bytes();(out/'candidate.atr').write_bytes(initial)
    lines=['Atari800 event recording, version: 1','122323']
    for f in range(1,total+10):
        pins=dict(stick=15,fire=1,consol=7,key=-1)
        for start,end,values in events:
            if start<=f<=end:pins.update(values)
        lines += [f"{pins['key']} 0 {pins['consol']}",str(240|pins['stick']),'255',str(pins['fire']),'1','1','1','00000000']
    with gzip.open(out/'input.gz','wt') as z:z.write('\n'.join(lines)+'\n')
    config=Path(os.environ['ENERGY_FIX1_CONFIG']).resolve();text=config.read_text()
    text=re.sub(r'^(ROM_[A-Z0-9_/]+)=(.+)$',lambda m:m[1]+'='+str((config.parent/Path(m[2])).resolve()) if not m[2].startswith(('UNSET','/')) else m[0],text,flags=re.M)
    for key,val in dict(RAM_SIZE=64,TURBO_SPEED=0,SOUND_ENABLED=int(audio),ENABLE_SIO_PATCH=0,VIDEOMODE_WINDOWED=1).items():
        text=re.sub('^'+key+'=.*\n?','',text,flags=re.M)+f'\n{key}={val}\n'
    cfg=out/'emulator.cfg';cfg.write_text(text)
    command=[os.environ['ENERGY_FIX1_OBSERVER'],'-config',str(cfg),'-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-sound' if audio else '-nosound','-nopatch','-windowed','-win-width','640','-win-height','480','-no-bilinear-filter','-turbo','-nortime','-pal-artif','none','-scanlines','0','-no-scanlinesint','-no-showstats','-playback',str(out/'input.gz'),'-playbacknoexit',str(play)]
    if realtime:command.remove('-turbo')
    env={k:v for k,v in os.environ.items() if not k.startswith(('NS65_','NSQ_','HWVIS_','PMG1_','INDUSTRIAL_','UX1_'))}
    env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NS65_OUTPUT=str(out),NS65_SP=f"{l['sp']:x}",NS65_CAPTURE=','.join(map(str,frames)),NS65_LIMIT=str(total),NS65_ISRS=','.join(f'{l[k]:x}' for k in ('_native_vbi','_vbi_end','_background_update','_background_end','_native_dli','_dli_end')),NS65_MARKERS=f"{l['_main']:x},ffff,ffff",HWVIS_ADDRS=','.join(f'{l[k]:x}' for k in ('_native_dli','dli_row','_asset_loading','_phase','_native_vbi'))+',0')
    env['NS65_ROUTINES']=','.join(f'{l[n]:x}' for n in ('neon_tick','neon_dma','neon_prepare'))+',0,0,0,0,0'
    if audio:env.update(NS65_AUDIO=str(out/'actual.wav'),UX1_AUDIO_START_FRAME='4500')
    with (out/'emulator.log').open('w') as log:r=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    assert r.returncode==0,(name,r.returncode)
    effective=json.loads((out/'hwvis-effective.json').read_text());assert effective['ram_kb']==64 and effective['tv_lines']==312 and effective['sio_patch']==0 and effective['basic_disabled']==1
    timing=json.loads((out/'timing.json').read_text());assert timing['csp_outside_samples']==0
    ss={};rasters=0
    for f in frames:
        raw=(out/f'frame-{f:04}.ram').read_bytes();s=state(raw,l);ss[f]=s
        if s['phase'] in (1,2) and s['pmg_active'] and not s['asset_loading']:
            rasters+=int(pixel(out,f,l,initial))
            area=s['scene']//15
            if not baseline:
                music=(b/f'music-{area+1}.nrq').read_bytes()[144:]
                assert raw[0x1800:0x1e10]==music,(name,f,'wrong music',area)
        assert sha(master)==master_digest
    summary=dict(status='PASS',master_sha256=sha(master),events=events,frames=frames,states=ss,rasters=rasters,timing=timing,effective=effective,audio=audio)
    dump(out/'summary.json',summary);print(name,'PASS',len(frames),'frames',flush=True)
    return out,ss,l

def memory(b):
    seg={n:(int(a,16),int(size,16)) for n,a,end,size,align in re.findall(r'^([A-Z_0-9]+)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{5})$',(b/'candidate.map').read_text(),re.M)}
    end=lambda n:sum(seg[n])
    return dict(MAIN_free=0x8000-end('BSS'),LOW_free=0x1400-end('LOADBSS'),ZP_free=0x100-end('ZEROPAGE'),PERSIST_free=0x9800-end('PERSIST'),EXTRA_free=0x2000-end('EXTRA'),CODE=seg['CODE'][1],RODATA=seg['RODATA'][1],BSS=seg['BSS'][1],LOADBSS=seg['LOADBSS'][1],C_stack=seg['CSTACK'][1],hardware_stack=256,fonts=2048,PMG=2048,music=1552)

def static():
    old=ROOT/'build/atmosphere1-baseline';b=BASE/'normal-r2';disk=(b/'candidate.atr').read_bytes();prior=(old/'candidate.atr').read_bytes()
    assert sha(old/'candidate.atr')=='a22992f1c4350d0e5c72150c6902aefdd2f485c3be5979f9da2a7bc2d32f3407'
    assert disk[16+999*128:16+1000*128]==prior[16+999*128:16+1000*128]
    for i in range(60):
        at=16+(1099+i*70)*128;assert disk[at:at+128]==prior[at:at+128]
        a,z=sec(disk,i),sec(prior,i);assert a[0xb160]==z[0xb160]
        for bank in (0,1):
            af=a[(0x8c00,0xa000)[bank]];zf=z[(0x8c00,0xa000)[bank]]
            for k in range(24):
                ac=a[0x9de0][8+bank*24+k];zc=z[0x9de0][8+bank*24+k]
                assert ac&128==zc&128
                assert af[(ac&127)*8:(ac&127)*8+8]==zf[(zc&127)*8:(zc&127)*8+8]
                # No object uses changed PF0: only background/steel and PF1/PF3.
                assert all(((v>>shift)&3)!=1 for v in af[(ac&127)*8:(ac&127)*8+8] for shift in (0,2,4,6))
        assert a[0x9de0][192:290]==z[0x9de0][160:258]
        assert a[0x9de0][541:]==z[0x9de0][541:]
    for key in ('move.s','undo-fast.s','campaign.c','phase.s','render.s','input.c','sio.s','loading.s','loading-text.s','early-support.s'):
        assert (b/'source'/key).read_bytes()==(old/'source'/key).read_bytes(),key
    previous=(old/'source/hardware.s').read_text();current=(b/'source/hardware.s').read_text()
    # Includes native DLI/VBI, input admission, DMA publication and robot hooks.
    assert previous[:previous.index('background_update:\n')]==current[:current.index('background_update:\n')]
    previous=(old/'source/display.c').read_text();current=(b/'source/display.c').read_text()
    assert previous[previous.index('static void activate(void)'):]==current[current.index('static void activate(void)'):]
    # Menu and splash packages remain byte-identical, as does the Energy score.
    for name in ('menu.nrq','splash.nrq','music.nrq'):assert (b/name).read_bytes()==(old/name).read_bytes(),name
    music=[(b/f'music-{i}.nrq').read_bytes() for i in range(1,5)];assert len(set(music))==4
    assert music[0]==(old/'music.nrq').read_bytes()
    glyphs=[json.loads(p.read_text())['fonts'] for p in b.glob('art-area-*/level-*/scene-0-industrial.json')]
    mem=memory(b);assert min(mem[k] for k in ('MAIN_free','LOW_free','ZP_free','PERSIST_free','EXTRA_free'))>=0
    variants=[]
    for m in ('01','16','31','46'):
        v=BASE/('test-'+m+'-r2');raw=(v/'candidate.atr').read_bytes()
        for i in range(60):
            at=16+(1099+i*70)*128;assert raw[at:at+128]==disk[at:at+128]
            assert {k:x for k,x in sec(raw,i).items() if k!=0xa400}=={k:x for k,x in sec(disk,i).items() if k!=0xa400}
        for i in range(1,5):assert (v/f'music-{i}.nrq').read_bytes()==music[i-1]
        variants.append(dict(mode=m,sha256=sha(v/'candidate.atr'),memory=memory(v)))
    dump(DOC/'static.json',dict(status='PASS',before=memory(old),after=mem,variants=variants,unchanged_maps=60,robot_masks_identical=True,crate_goal_pixels_and_colors_identical=True,menu_splash_energy_score_identical=True,font_max=[max(f[i]['glyphs'] for f in glyphs) for i in range(2)],music_sha256=[hashlib.sha256(x[144:]).hexdigest() for x in music]))
    print('static PASS',mem,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('case',choices=('static','preview'));a=p.parse_args()
    if a.case=='static':static()
    else:probe('preview','normal',[(3200,3200,dict(fire=0))],[4500,4550,4600],4620)
