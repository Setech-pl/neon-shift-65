#!/usr/bin/env python3
"""Capture actual ATR cold boots headlessly; encode 2x NN GIFs at original PAL time.
Requires Atari800 7.1.2 with the repository read-only NS65 observer, ffmpeg,
NEON_ATARI800 and NEON_ATARI_CONFIG (private, legally supplied ROM config).
Raw PNG/RAM/logs remain under ignored build/owner-smoke/media/.
"""
import argparse,gzip,hashlib,json,os,re,shutil,subprocess,struct
from pathlib import Path
from publish1_prepare import ROOT,PRODUCT,HASHES,blob,main as prepare
PAL=1773447/35568

def call(cmd,**kw):subprocess.run(list(map(str,cmd)),check=True,**kw)
def main(owner_folder='build/owner-smoke', work_folder='build/owner-smoke/media', stock=False):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--encode-only',action='store_true');a=p.parse_args()
    exe=Path(os.environ['NEON_ATARI800']).resolve();cfg=Path(os.environ['NEON_ATARI_CONFIG']).resolve()
    dest=ROOT/'docs/media';dest.mkdir(parents=True,exist_ok=True)
    work=ROOT/work_folder;work.mkdir(parents=True,exist_ok=True)
    levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
    label_records=json.loads((dest/'capture-labels.json').read_text())
    records=[];montage=[]
    for area,n in enumerate((0,16,31,46),1):
        out=work/f'area-{area}';out.mkdir(exist_ok=True)
        src=ROOT/'dist/neon-shift65-v1.0.0.atr' if not n else ROOT/owner_folder/(f'neon-shift65-hwvis1-test-{n:02}.atr' if stock else f'neon-shift65-v1.0.0-test-{n:02}.atr')
        data=src.read_bytes();assert hashlib.sha256(data).hexdigest()==HASHES[n]
        events=[(700,{'fire':0}),(1000,{'stick':7}),(1040,{'stick':7}),(1080,{'consol':5}),(1120,{'stick':7}),(1220,{'fire':0})] if not n else []
        if stock and not n:events=[(f+3600,v) for f,v in events];events[0]=(3200,events[0][1])
        first=(4580 if not n else 3000) if stock else (980 if not n else 1000)
        if n:
            events += [(first+20+i*20,{'stick':{'U':14,'D':13,'L':11,'R':7}[c]}) for i,c in enumerate(levels[n-1]['path'][:6])]
            events += [(first+160,{'fire':0})]
        frames=list(range(first,first+200,5));screens={'energy':1600,'menu':650,'loader':750} if not n else {('hydro','data','reactor')[area-2]:first}
        if stock and not n:screens={'energy':5600,'menu':2750,'loader':3500}
        captures=sorted(set(frames+list(screens.values())))
        label_record=label_records[str(n)];labels=label_record['text'].encode()
        assert hashlib.sha256(labels).hexdigest()==label_record['sha256']
        labs={m[2]:int(m[1],16) for m in re.finditer(r'^al ([a-fA-F0-9]+) \.([\w]+)',labels.decode(),re.M)}
        if not a.encode_only:
            (out/'play.atr').write_bytes(data)
            lines=['Atari800 event recording, version: 1','122323']
            for f in range(1,max(captures)+30):
                pins=next((v for frame,v in events if frame==f),{})
                lines.extend([f"-1 0 {pins.get('consol',7)}",str(240|pins.get('stick',15)),'255',str(pins.get('fire',1)),'1','1','1','00000000'])
            with gzip.open(out/'input.gz','wt') as z:z.write('\n'.join(lines)+'\n')
            text=cfg.read_text();text=text.replace('TURBO_SPEED=1','TURBO_SPEED=0').replace('SOUND_ENABLED=1','SOUND_ENABLED=0')
            if stock:text=text.replace('ENABLE_SIO_PATCH=1','ENABLE_SIO_PATCH=0')
            (out/'emulator.cfg').write_text(text)
            env={k:v for k,v in os.environ.items() if not k.startswith(('NS65_','NSQ_','UX1_','ENG2_'))}
            env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NS65_OUTPUT=str(out),NS65_CAPTURE=','.join(map(str,captures)),NS65_LIMIT=str(max(captures)+10),NS65_SP=f"{labs['sp']:04x}")
            argv=[exe,'-config',out/'emulator.cfg','-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-nortime','-windowed','-win-width','640','-win-height','480','-no-bilinear-filter','-scanlines','0','-no-scanlinesint','-turbo','-playback',out/'input.gz','-playbacknoexit','-screenshots',out/'native-###.png',out/'play.atr']
            if stock:argv.append('-nopatch')
            with (out/'emulator.log').open('w') as log:call(argv,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        for f in captures:
            path=out/f'native-{f:04}.png';assert path.is_file(),(area,f)
            assert struct.unpack('>II',path.read_bytes()[16:24])==(336,240),'Require uncropped capture: use explicit window dimensions with SDL dummy'
        for i,f in enumerate(frames):shutil.copyfile(out/f'native-{f:04}.png',out/f'clip-{i:03}.png')
        def encode(inputs,output):
            call(['ffmpeg','-v','error','-y','-framerate',str(PAL/5),'-i',inputs,'-filter_complex','scale=iw*2:ih*2:flags=neighbor,split[a][b];[a]palettegen=max_colors=256:reserve_transparent=0[p];[b][p]paletteuse=dither=none','-loop','0',output])
        encode(out/'clip-%03d.png',dest/f'area-{area}.gif')
        for f in frames:
            target=work/f'montage-{len(montage):03}.png';shutil.copyfile(out/f'native-{f:04}.png',target);montage.append(f)
        for name,f in screens.items():call(['ffmpeg','-v','error','-y','-i',out/f'native-{f:04}.png','-vf','scale=iw*2:ih*2:flags=neighbor','-frames:v','1','-pix_fmt','rgb24',dest/(name+'.png')])
        states=[]
        for f in (frames[0],frames[-1]):
            ram=(out/f'frame-{f:04}.ram').read_bytes();states.append({'frame':f,'phase':ram[labs['_phase']],'scene':ram[labs['_scene']]})
        records.append({'area':area,'level':n or 1,'source_atr_sha256':HASHES[n],'test_start':bool(n),'inputs':[{'frame':f,'pins':v} for f,v in events],'gif_frames':frames,'screenshots':screens,'endpoint_states':states})
    encode(work/'montage-%03d.png',dest/'neon-shift65.gif')
    manifest={'product_commit':PRODUCT,'normal_atr_sha256':HASHES[0],'emulator':{'name':'Atari800','version':'7.1.2','binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'observer':'NS65 read-only capture; no game memory injection','private_config_sha256':hashlib.sha256(cfg.read_bytes()).hexdigest(),'settings':'XL/XE PAL64, BASIC/MAPRAM/stereo off; '+('standard OS SIO (-nopatch)' if stock else 'SIO patch on')+'; SDL video/audio dummy; turbo host pacing only'},'time':{'pal_fps':PAL,'sample_every_frames':5,'gif_fps':PAL/5,'duration_seconds':800/PAL,'note':'GIF centisecond rounding only; no speedup'},'scaling':'336x240 -> 672x480, integer 2x nearest-neighbour; paletteuse dither=none; no retouch or smoothing','montage':'4 separate 200-PAL-frame excerpts in Energy/Hydro/Data/Reactor order; hard cuts, not continuous travel','variant_equivalence':'See product-equivalence.json; campaign/assets equal; test code differs only by startup and save namespace (not byte-identical executable). Normal game has no area-select.','runs':records,'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(dest.iterdir()) if p.suffix in ('.gif','.png')}}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('PASS real cold ATR captures, five GIFs and six PNGs')
if __name__=='__main__':main()
