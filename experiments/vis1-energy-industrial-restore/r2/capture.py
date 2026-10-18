#!/usr/bin/env python3
"""Paired cold-boot ATR captures through legal input, with identical PAL config.

Uses existing read-only Atari800 observer. No state injection or target writes.
The normal replay and fixture selector are the baseline's existing routes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / 'build/vis1-energy-industrial-restore/r2'
sys.path.insert(0, str(ROOT / 'tools'))
from emulator_smoke import run

# The baseline's host pacing, made explicit here without importing an untracked
# experiment helper. Only host speed changes; target remains 35568 clocks/PAL.
original_run = subprocess.run


def paced(argv, *args, **kwargs):
    if isinstance(argv, list) and argv and str(argv[0]).endswith('/atari800'):
        argv = list(argv) + ['-turbo']
        cfg = Path(argv[argv.index('-config') + 1])
        cfg.write_text(cfg.read_text().replace('TURBO_SPEED=1', 'TURBO_SPEED=0'))
        (cfg.parent/'command.json').write_text(json.dumps(argv,indent=2)+'\n')
        (cfg.parent/'host-pacing.json').write_text(json.dumps(dict(
            mode='-turbo, TURBO_SPEED=0',target='Same PAL35568 clocks/frame; no target code/input modifications'),indent=2)+'\n')
    return original_run(argv, *args, **kwargs)


subprocess.run = paced


def labels(path):
    return {n: int(h, 16) for h, n in re.findall(r'al (\w+) \.(\w+)', path.read_text())}


def state(ram, l):
    g = l['_gs']
    boxes = [list(ram[g + 764 + 2*i:g + 766 + 2*i]) for i in range(ram[g + 784])]
    goals = {(x, y) for y in range(ram[g + 761]) for x in range(ram[g + 760])
             if ram[g + y*38 + x] == 46}
    return dict(phase=ram[l['_phase']], scene=ram[l['_scene']],
        loading=ram[l['_asset_loading']], error=ram[l['_error']],
        player=list(ram[g + 762:g + 764]), boxes=boxes,
        docked=sum(tuple(b) in goals for b in boxes),
        moves=int.from_bytes(ram[g + 785:g + 789], 'little'),
        pushes=int.from_bytes(ram[g + 789:g + 793], 'little'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('variant', choices=['baseline', 'candidate'])
    p.add_argument('--case', choices=['review', 'response'], default='review')
    a = p.parse_args()
    os.chdir(ROOT)
    source = ROOT / 'build/vis1-energy-industrial-restore/r2/baseline/area-1' if a.variant == 'baseline' else BUILD / 'area-1'
    for k in list(os.environ):
        if k.startswith(('NSQ_', 'NS65_', 'UX1_', 'ENG2_BUS_', 'ENG3_MISSING_')):
            os.environ.pop(k, None)
    os.environ['NEON_ATARI800'] = str(ROOT / 'build/eng3-observed-input-3pal/observer/src/atari800')
    os.environ['NEON_ATARI_CONFIG'] = str(ROOT / 'build/visual-baseline/capture-base.cfg')
    l = labels(source / 'candidate.lbl')
    os.environ['NSQ_STATE'] = ','.join(f'{l[n]:04x}' for n in [
        '_asset_loading', '_audio_calls', '_input_head', '_input_tail',
        'order_index', 'music_row', 'music_tick'])
    events = [(700, 700, dict(fire=0))]
    if a.case == 'review':
        solution = (ROOT / 'experiments/eng3-observed-input-3pal/energy-service-bay-obstacles-v1.solution').read_text().strip()
        events += [(1000+i*16, 1000+i*16, dict(stick={'R':7,'L':11,'U':14,'D':13}[c]))
                   for i, c in enumerate(solution)]
        events += [(2160,2160,dict(consol=6)), (2200,2200,dict(fire=0)),
            (2260,2260,dict(consol=6)), (2300,2300,dict(consol=5)),
            (2540,2540,dict(stick=13)), (2580,2580,dict(fire=0)),
            (2920,2920,dict(consol=6)), (2960,2960,dict(stick=7)),
            (3000,3000,dict(consol=3)), (3400,3400,dict(consol=6)),
            (3440,3440,dict(stick=7)), (3480,3480,dict(consol=3)),
            (3840,3840,dict(stick=11))]
        captures = sorted(set([200,450,570,780,950,1220,2120,2180,2220,2880,
                                3340,3780,3860] + list(range(950,991))))
        total = 3890
    else:
        # First R pushes a crate. FIRE undoes; U then hits the metal wall.
        events += [(1000,1000,dict(stick=7)), (1040,1040,dict(fire=0)),
                   (1080,1080,dict(stick=14))]
        captures = list(range(990,1091))
        total = 1100
    out = run(str((BUILD / 'captures' / f'{a.variant}-{a.case}').relative_to(ROOT / 'build')),
        events, captures, total, xex=str(source / 'candidate.xex'),
        labels_path=str(source / 'candidate.lbl'), atr=str(source / 'candidate.atr'),
        boot=True, sio_patch=True,
        routines=['_game_step','_undo_pop','_display_counters','_publish_now',
                  '_frame_audio','_background_update'])
    states = {str(f): state((out / f'frame-{f:04}.ram').read_bytes(), l) for f in captures}
    (out / 'states.json').write_text(json.dumps(states, indent=2)+'\n')
    (out / 'route.json').write_text(json.dumps(dict(events=events, captures=captures,
        total=total, config=str(ROOT / 'build/visual-baseline/capture-base.cfg'),
        config_sha256=hashlib.sha256((out / 'emulator.cfg').read_bytes()).hexdigest(),
        method='Cold boot ATR + legal device playback, no game memory injection'), indent=2)+'\n')
    show = [950,1220,2120,3340,3780,3860] if a.case == 'review' else [990,1020,1060,1090]
    print(json.dumps({f:states[str(f)] for f in show}, indent=2))


if __name__ == '__main__':
    main()
