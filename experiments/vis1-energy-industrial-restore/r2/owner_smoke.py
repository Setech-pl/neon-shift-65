#!/usr/bin/env python3
"""VIS1 owner WINDOWED launcher. Agent uses --check only; never autosaves config."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / 'build/vis1-energy-industrial-restore/r2'
DOCS = ROOT / 'docs/checkpoints/vis1-energy-industrial-restore/r2'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--check',action='store_true')
    p.add_argument('--physical-joystick',action='store_true')
    a=p.parse_args()
    emulator=shutil.which('atari800')
    default=ROOT/'build/visual-baseline/capture-base.cfg'
    if not default.exists():
        default=DOCS.parent/'capture-base.cfg'
    cfg=Path(os.environ.get('NEON_ATARI_CONFIG',str(default))).expanduser()
    artifact=BUILD/'area-1/candidate.atr'
    if not artifact.exists():
        artifact=DOCS/'owner-smoke/neon-shift65-vis1-r2-energy.atr'
    if not emulator or not cfg.exists() or not artifact.exists():
        raise SystemExit('Wymagany Atari800, ATR VIS1 i konfiguracja XL OS ROM.')
    digest=hashlib.sha256(artifact.read_bytes()).hexdigest()
    frozen=DOCS/'manifest.json'
    if frozen.exists():
        assert digest==json.loads(frozen.read_text())['candidate_ATR_sha256'], 'ATR differs from owner review freeze'
    text=cfg.read_text()
    def set_value(key,value):
        nonlocal text
        text=re.sub(r'^'+re.escape(key)+r'=.*\n?','',text,flags=re.M)
        text=text.rstrip('\n')+'\n'+key+'='+str(value)+'\n'
    for key,value in dict(RAM_SIZE=64,TURBO_SPEED=0,SOUND_ENABLED=1,ENABLE_SIO_PATCH=0,
        VIDEOMODE_WINDOWED=1,VIDEOMODE_STRETCH='INTEGRAL',BILINEAR_FILTERING=0,
        ARTIFACT_PAL='NONE',SCANLINES_PERCENTAGE=0,INTERPOLATE_SCANLINES=0).items():
        set_value(key,value)
    for prefix in ('SDL2_','SDL_'):
        for key,value in dict(JOY_0_UP=119,JOY_0_DOWN=115,JOY_0_LEFT=97,
                             JOY_0_RIGHT=100,JOY_0_TRIGGER=109).items():
            set_value(prefix+key,value)
    out=BUILD/'owner-smoke';out.mkdir(parents=True,exist_ok=True)
    (out/'emulator.cfg').write_text(text)
    argv=[emulator,'-config',str(out/'emulator.cfg'),'-no-autosave-config',
        '-xl','-pal','-nobasic','-no-mapram','-nostereo','-sound','-nopatch',
        '-windowed','-no-bilinear-filter','-pal-artif','none','-scanlines','0',
        '-no-scanlinesint','-no-showstats']
    if not a.physical_joystick:
        argv.append('-kbdjoy0')
    argv.append(str(artifact))
    record=dict(command=argv,display_mode='WINDOWED',ATR_sha256=digest,
        boot='ATR cold boot D1; OS SIO without patch',
        config_source=str(cfg),config_autosave=False,owner_visual='OWNER NOT_RUN')
    (out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
    if a.check:
        print(json.dumps(record,indent=2))
        return 0
    return subprocess.call(argv)


if __name__=='__main__':
    raise SystemExit(main())
