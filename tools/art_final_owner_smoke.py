#!/usr/bin/env python3
"""Launch the single v1.0 ART-FINAL candidate WINDOWED; agent uses --check."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--physical-joystick',action='store_true')
    a=p.parse_args()
    cmd=[sys.executable,str(ROOT/'tools/product1_owner_smoke.py'),
         '--atr',str(ROOT/'docs/art-final/owner-smoke/neon-shift65-v1-art-final.atr'),
         '--emulator',str(ROOT/'build/eng3-observed-input-3pal/observer/src/atari800'),
         '--config',str(ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg'),
         '--output',str(ROOT/'build/art-final/owner-smoke')]
    if a.check:cmd.append('--check')
    if a.physical_joystick:cmd.append('--physical-joystick')
    return subprocess.call(cmd)


if __name__=='__main__':raise SystemExit(main())
