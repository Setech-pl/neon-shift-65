#!/usr/bin/env python3
"""Portable WINDOWED owner launcher. --check prepares files without a GUI."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
def main():
    here=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atr',type=Path,default=here/'neon-shift65-product1.atr')
    p.add_argument('--emulator',default=os.environ.get('NEON_ATARI800') or shutil.which('atari800'))
    p.add_argument('--config',type=Path,default=os.environ.get('NEON_ATARI_CONFIG'))
    p.add_argument('--output',type=Path,default=here/'owner-smoke')
    p.add_argument('--physical-joystick',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if not a.emulator or not a.config or not a.config.is_file() or not a.atr.is_file():
        p.error('Provide Atari800 --emulator, an owner XL OS ROM --config and the supplied --atr. No ROM is included.')
    exe=Path(a.emulator).expanduser().resolve();cfg=a.config.expanduser().resolve();atr=a.atr.expanduser().resolve()
    if not exe.is_file():p.error('Emulator path does not exist')
    text=cfg.read_text()
    # Resolve ROM paths against the supplied config, so the bundle is movable.
    def paths(m):
        key,value=m.groups();value=value.strip()
        if value and not value.startswith('UNSET'):
            q=Path(value).expanduser()
            if not q.is_absolute():q=cfg.parent/q
            value=str(q.resolve())
        return key+'='+value
    text=re.sub(r'^(ROM_[A-Z0-9_/]+)=(.*)$',paths,text,flags=re.M)
    def put(key,value):
        nonlocal text
        text=re.sub(r'^'+re.escape(key)+r'=.*\n?','',text,flags=re.M).rstrip('\n')+'\n'+key+'='+str(value)+'\n'
    for k,v in dict(RAM_SIZE=64,TURBO_SPEED=0,SOUND_ENABLED=1,ENABLE_SIO_PATCH=0,VIDEOMODE_WINDOWED=1,BILINEAR_FILTERING=0,ARTIFACT_PAL='NONE',SCANLINES_PERCENTAGE=0,INTERPOLATE_SCANLINES=0).items():put(k,v)
    for prefix in ('SDL2_','SDL_'):
        for k,v in dict(JOY_0_UP=119,JOY_0_DOWN=115,JOY_0_LEFT=97,JOY_0_RIGHT=100,JOY_0_TRIGGER=109).items():put(prefix+k,v)
    out=a.output.expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
    local_cfg=out/'emulator.cfg';local_cfg.write_text(text)
    play=out/'neon-shift65-play.atr'
    if not play.exists():shutil.copyfile(atr,play)
    argv=[str(exe),'-config',str(local_cfg),'-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-sound','-nopatch','-windowed','-win-width','640','-win-height','480','-no-bilinear-filter','-pal-artif','none','-scanlines','0','-no-scanlinesint','-no-showstats']
    if not a.physical_joystick:argv.append('-kbdjoy0')
    argv.append(str(play))
    record=dict(command=argv,display='WINDOWED',target='Atari 65XE/XL PAL 64 KB',boot='D1 ATR, OS SIO, no patch',supplied_atr_sha256=hashlib.sha256(atr.read_bytes()).hexdigest(),play_disk=str(play),progress='existing play disk retained',controls='WASD + M (FIRE), F2 OPTION, F3 SELECT, F4 START; or joystick')
    (out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
    if a.check:print(json.dumps(record,indent=2));return 0
    return subprocess.call(argv)
if __name__=='__main__':raise SystemExit(main())
