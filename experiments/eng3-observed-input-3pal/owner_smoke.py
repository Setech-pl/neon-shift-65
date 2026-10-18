#!/usr/bin/env python3
"""Explicit windowed candidate ATR launch; --check never launches a GUI."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('--area',type=int,choices=[1,2,3,4],required=True);p.add_argument('--check',action='store_true');p.add_argument('--physical-joystick',action='store_true');p.add_argument('--variant',choices=['candidate','dim','stress','carry','wrap','counter9','counter99'],default='candidate');a=p.parse_args()
    cfg=Path(os.environ.get('NEON_ATARI_CONFIG',str(ROOT/'docs/audit/evidence-2026-10-08-160947/runtime-pal-final/emulator.cfg'))).expanduser()
    emulator=shutil.which('atari800')
    if not emulator or not cfg.exists():raise SystemExit('Wymagany Atari800 i NEON_ATARI_CONFIG z XL OS ROM.')
    text=cfg.read_text()
    def set_value(key,value):
        nonlocal text
        text=re.sub(r'^'+re.escape(key)+r'=.*\n?','',text,flags=re.M);text=text.rstrip('\n')+'\n'+key+'='+str(value)+'\n'
    for key,value in dict(RAM_SIZE=64,TURBO_SPEED=0,SOUND_ENABLED=1,ENABLE_SIO_PATCH=0,VIDEOMODE_WINDOWED=1,BILINEAR_FILTERING=0,ARTIFACT_PAL='NONE',SCANLINES_PERCENTAGE=0,INTERPOLATE_SCANLINES=0).items():set_value(key,value)
    for prefix in ['SDL2_','SDL_']:
        for key,value in dict(JOY_0_UP=119,JOY_0_DOWN=115,JOY_0_LEFT=97,JOY_0_RIGHT=100,JOY_0_TRIGGER=109).items():set_value(prefix+key,value)
    out=ROOT/f'build/eng3-observed-input-3pal/area-{a.area}/owner-smoke';out.mkdir(parents=True,exist_ok=True);(out/'emulator.cfg').write_text(text)
    artifact=ROOT/f'build/eng3-observed-input-3pal/area-{a.area}'/f'{a.variant}.atr'
    argv=[emulator,'-config',str(out/'emulator.cfg'),'-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-sound','-nopatch','-windowed','-no-bilinear-filter','-pal-artif','none','-scanlines','0','-no-scanlinesint','-no-showstats']
    if not a.physical_joystick:argv.append('-kbdjoy0')
    argv.append(str(artifact))
    record=dict(command=argv,display_mode='windowed',boot='ATR cold boot D1; OS SIO without patch',sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
    (out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
    if a.check:print(json.dumps(record,indent=2));return 0
    return subprocess.call(argv)
if __name__=='__main__':raise SystemExit(main())
