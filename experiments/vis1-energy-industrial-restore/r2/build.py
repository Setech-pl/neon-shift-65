#!/usr/bin/env python3
"""Build VIS1 with ENG3's exact build path plus an offline Energy art overlay.

Copies the frozen experiment into this run's build directory. The only adapter
is the explicit install() call at the end of its compile.py. ENG3 sources and all
pre-existing outputs remain untouched. Areas2–4 can be compiled for byte audits.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'experiments/eng3-observed-input-3pal'
BUILD = ROOT / 'build/vis1-energy-industrial-restore/r2'
REFERENCE_SHA = '8b8c930a747167cef2d40eebb506271c0d552f77936abd24bb3f8c6248d50a2c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--area', type=int, choices=range(1, 5), default=1)
    a = p.parse_args()
    os.chdir(ROOT)
    reference = ROOT / 'reference/vis1-owner/energy-owner-reference.png'
    assert sha(reference) == REFERENCE_SHA, 'Primary owner reference SHA mismatch'
    out = BUILD / f'area-{a.area}'
    out.mkdir(parents=True, exist_ok=True)
    source = out / 'source'
    shutil.copytree(BASE, source, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    compiler = source / 'compile.py'
    marker = "if __name__=='__main__':main()"
    text = compiler.read_text()
    assert text.count(marker) == 1
    compiler.write_text(text.replace(marker,
        "import vis1_energy\nvis1_energy.install(sys.modules[__name__])\n" + marker))
    shutil.copyfile(HERE / 'energy.py', source / 'vis1_energy.py')
    shutil.copyfile(HERE.parent / 'energy.py', source / 'vis1_base.py')
    env = dict(os.environ, NEON_ART2_BUILD=str(out), NEON_ART2_AREA=str(a.area),
               NEON_ART2_FIXTURE='obstacles', ART3_VARIANT='B')
    subprocess.run([sys.executable, str(source / 'build.py')], env=env, check=True)
    inputs = list(BASE.rglob('*')) + list((ROOT / 'src').glob('*')) + [
        HERE / 'build.py', HERE / 'energy.py', HERE.parent / 'energy.py', ROOT / 'tools/assets.py',
        ROOT / 'tools/warehouses.py', ROOT / 'tools/solver.py', ROOT / 'tools/atr.py',
        ROOT / 'assets/levels/prototypes.json',
        ROOT / 'assets/graphics/mono-font.json', ROOT / 'assets/graphics/pal-palette.json',
        reference]
    records = {str(f.relative_to(ROOT)): sha(f) for f in inputs
               if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc'}
    # Distinguish the archived ENG3 dependency inventory from files actually
    # consumed by this build. artwork.py and Node retain their pinned root paths.
    used = [HERE/'build.py', HERE/'energy.py', HERE.parent/'energy.py']
    used += [BASE/n for n in (
        'build.py','compile.py','artwork.py','themes.py','decoration.py','areas.json',
        'early.py','loading_art.py','splash_assets.py','boot-splash.json',
        'main.c','display.c','loader.c','input.c','input_atari.c','validate.c',
        'loading.s','hardware.s','render.s','header.s','sio.s','crc.s','move.s',
        'phase.s','regions.s','undo-fast.s','boot.s','splash.s','early-support.s',
        'loading-text.s','boot.cfg','link.cfg',
        'energy-service-bay-obstacles-v1.xsb','energy-service-bay-obstacles-v1.solution',
        'reference/prototype_assets.c','reference/broadside-lzss.mjs',
        'reference/boot-splash-assets.mjs','reference/void-loader.json',
        'candidate.h','hardware.h')]
    used += [ROOT/'src'/n for n in ('level.h','game.h','undo.h','input.h')]
    used += [ROOT/n for n in ('src/level.c','src/game.c','src/undo.c',
        'tools/assets.py','tools/warehouses.py','tools/solver.py','tools/atr.py',
        'assets/levels/prototypes.json','assets/graphics/mono-font.json',
        'assets/graphics/pal-palette.json')]
    generated = [source/'compile.py',source/'vis1_energy.py',source/'vis1_base.py']
    generated += list((out/'cc-input').glob('*.c'))
    generated += [out/n for n in ('level.c','undo.c','assets.c','aliases.s','numfont.s',
        'prototype_assets.h','neon-palette.h','neon-palette.inc','boot-splash.inc',
        'splash-data.inc','splash-data.h','early-support.s','early-splash.s','early.cfg',
        'early-text.cfg','replay.c')]
    (out / 'source-manifest.json').write_text(json.dumps(dict(
        base_commit='9dab4368f446804d79e514e56c8fb90f5c324b38',
        area=a.area, configuration=dict(NEON_ART2_AREA=a.area, NEON_ART2_FIXTURE='obstacles', ART3_VARIANT='B'), build_command=f'python3 experiments/vis1-energy-industrial-restore/r2/build.py --area {a.area}',
        adapter='Copy ENG3, inject offline vis1_energy.install into compile.py only',
        inputs=records, inventory_note='inputs is the full inherited dependency inventory; not every archived harness is executed',
        actually_used_sources={str(f.relative_to(ROOT)):sha(f) for f in used},
        generated_build_inputs={str(f.relative_to(ROOT)):sha(f) for f in generated},
        primary_owner_reference=dict(path=str(reference.relative_to(ROOT)),sha256=sha(reference),role='Visual reference, not compiler pixel input'),
        generated_compiler_sha256=sha(compiler),
        ATR_sha256=sha(out / 'candidate.atr')), indent=2) + '\n')


if __name__ == '__main__':
    main()
