#!/usr/bin/env python3
"""RC2 WINDOWED owner launcher; agent uses --check only, stock OS SIO."""
import argparse
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--area',type=int,choices=(1,16,31,46))
    p.add_argument('--check',action='store_true');p.add_argument('--physical-joystick',action='store_true');a=p.parse_args()
    name='neon-shift65-v1.0-RC2'+(f'-test-{a.area:02}' if a.area else '')
    cmd=[sys.executable,str(ROOT/'tools/product1_owner_smoke.py'),'--atr',str(ROOT/'docs/finish2/owner-smoke'/(name+'.atr')),
         '--emulator',str(ROOT/'build/eng3-observed-input-3pal/observer/src/atari800'),
         '--config',str(ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg'),
         '--output',str(ROOT/'build/finish2/owner-smoke'/name)]
    if a.check:cmd.append('--check')
    if a.physical_joystick:cmd.append('--physical-joystick')
    return subprocess.call(cmd)
if __name__=='__main__':raise SystemExit(main())
