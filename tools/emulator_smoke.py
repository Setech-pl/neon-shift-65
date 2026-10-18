#!/usr/bin/env python3
"""PAL 64K Atari800 device playback, RAM-only evidence and native screenshots.
No writes to emulated game memory. Requires the owner's XL OS ROM config.
"""
import gzip,json,os,re,subprocess,sys,shutil,hashlib
from pathlib import Path

def run(name,events,captures,total=650,xex='build/neon-shift-65.xex',audio=False,labels_path='build/neon.lbl',atr=None,boot=False,routines=None,sio_patch=True):
    out=Path('build')/name;out.mkdir(parents=True,exist_ok=True);out=out.resolve()
    cfg=Path('docs/audit/evidence-2026-10-08-160947/runtime-pal-final/emulator.cfg')
    # Portable alternative: pass NEON_ATARI_CONFIG, with the same XL OS used by audit.
    cfg=Path(os.environ.get('NEON_ATARI_CONFIG',str(cfg))).resolve()
    if not cfg.exists():raise RuntimeError('Set NEON_ATARI_CONFIG to an XL PAL 64K Atari800 config')
    text=cfg.read_text().replace('TURBO_SPEED=0','TURBO_SPEED=1').replace('SOUND_ENABLED=1','SOUND_ENABLED=0')
    if audio:text=text.replace('SOUND_ENABLED=0','SOUND_ENABLED=1')
    if not sio_patch:text=text.replace('ENABLE_SIO_PATCH=1','ENABLE_SIO_PATCH=0')
    (out/'emulator.cfg').write_text(text)
    lines=['Atari800 event recording, version: 1','122323']
    for f in range(1,total+10):
        stick,fire,consol,key=15,1,7,-1
        for a,b,data in events:
            if a<=f<=b:
                stick=data.get('stick',stick);fire=data.get('fire',fire);consol=data.get('consol',consol);key=data.get('key',key)
        # Capture is read-only in the separate emulator, not a game key.
        lines.extend([f'{key} 0 {consol}',str(240|stick),'255',str(fire),'1','1','1','00000000'])
    with gzip.open(out/'input.gz','wt') as z:z.write('\n'.join(lines)+'\n')
    shutil.copyfile(xex,out/'candidate.xex')
    shutil.copyfile(labels_path,out/'candidate.lbl')
    if atr:shutil.copyfile(atr,out/'candidate.atr')
    artifact={'sha256':hashlib.sha256((out/'candidate.xex').read_bytes()).hexdigest(),'bytes':(out/'candidate.xex').stat().st_size,'captures':captures}
    if atr:artifact['ATR']=dict(sha256=hashlib.sha256((out/'candidate.atr').read_bytes()).hexdigest(),bytes=(out/'candidate.atr').stat().st_size)
    artifact['SIO_patch']=sio_patch;artifact['boot']='ATR' if boot else 'XEX'
    (out/'artifact.json').write_text(json.dumps(artifact,indent=2)+'\n')
    emulator=os.environ.get('NEON_ATARI800','/private/tmp/neon-shift-65-atari800/src/atari800')
    argv=[emulator,'-config',str(out/'emulator.cfg'),'-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-nortime','-windowed','-win-width','640','-win-height','480','-playback',str(out/'input.gz'),'-playbacknoexit','-record',str(out/'verified-input.gz'),'-screenshots',str(out/'native-###.png'),'-pokeyrec','-pokeyrec-ascii','-pokeyrec-file',str(out/'pokey.txt'),'-run',str(out/'candidate.xex')]
    if audio:argv.append('-sound')
    if boot:
        assert atr
        argv=argv[:-2] if argv[-2]=='-run' else argv
        if '-run' in argv:
            at=argv.index('-run');del argv[at:at+2]
    if atr:argv.append(str(out/'candidate.atr'))
    if not sio_patch:argv.append('-nopatch')
    (out/'command.json').write_text(json.dumps(argv,indent=2)+'\n')
    labels={m.group(2):int(m.group(1),16) for m in re.finditer(r'^al ([0-9A-Fa-f]+) \.([\w]+)',(out/'candidate.lbl').read_text(),re.M)}
    env=dict(os.environ,NS65_ISRS=','.join(f'{labels.get(k,65535):04x}' for k in ['_native_vbi','_vbi_end','_background_update','_background_end','_native_dli','_dli_end']),SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NS65_OUTPUT=str(out),NS65_SP=f'{labels["sp"]:04x}',NS65_CAPTURE=','.join(str(f) for f in captures),NS65_LIMIT=str(total),NS65_PROFILE=','.join(f'{labels.get(k,65535):04x}' for k in ['_frame_logic','_frame_audio','_frame_render']),NS65_MARKERS=','.join(f'{labels.get(k,65535):04x}' for k in ['_main','_frame_begin','_frame_end']))
    if audio:env['NS65_AUDIO']=str(out/'native-audio.wav')
    env['NS65_ROUTINES']=','.join(f'{labels.get(k,0):04x}' for k in (routines or ['_display_counters','_display_hud','_game_start','_game_step','_undo_pop','_display_changed','_display_animate','_display_board']))
    env['NS65_FLOW']=f'{labels.get("_flow",65535):04x}'
    if routines:env['NS65_WAREHOUSE']='1'
    with (out/'emulator.log').open('w') as log:
        r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,text=True,env=env,timeout=180)
    print(f'emulator exit={r.returncode} RAM captures={len(list(out.glob("frame-*.ram")))} native PNG={len(list(out.glob("*.png")))} at {out}')
    if r.returncode or not all((out/f'frame-{f:04}.ram').exists() and (out/f'native-{f:04}.png').exists() for f in captures):raise RuntimeError('emulator smoke failed')
    if routines:
        for name in ('routine-timing.json','hud-timing.json'):
            data=json.loads((out/name).read_text());data['names' if name.startswith('routine') else 'routines']=routines if name.startswith('routine') else routines[:2]
            (out/name).write_text(json.dumps(data,indent=2)+'\n')
    return out
if __name__=='__main__':
    run('m0-pal-native',[(150,153,dict(fire=0)),(240,245,dict(stick=7)),(300,304,dict(consol=5)),(400,405,dict(stick=11)),(500,503,dict(fire=0))],[120,200,280,340,460,560],600)
