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

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'experiments/eng3-observed-input-3pal'
BUILD = ROOT / 'build/vis1-energy-industrial-restore'
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
    env = dict(os.environ, NEON_ART2_BUILD=str(out), NEON_ART2_AREA=str(a.area))
    subprocess.run([sys.executable, str(source / 'build.py')], env=env, check=True)
    inputs = list(BASE.rglob('*')) + list((ROOT / 'src').glob('*')) + [
        HERE / 'build.py', HERE / 'energy.py', ROOT / 'tools/assets.py',
        ROOT / 'tools/warehouses.py', ROOT / 'tools/solver.py', ROOT / 'tools/atr.py',
        ROOT / 'assets/levels/prototypes.json',
        ROOT / 'assets/graphics/mono-font.json', ROOT / 'assets/graphics/pal-palette.json',
        reference]
    records = {str(f.relative_to(ROOT)): sha(f) for f in inputs
               if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc'}
    (out / 'source-manifest.json').write_text(json.dumps(dict(
        base_commit='5354212dcc9b8d0de5bea0299f4a1252f654d505',
        area=a.area, build_command=f'python3 experiments/vis1-energy-industrial-restore/build.py --area {a.area}',
        adapter='Copy ENG3, inject offline vis1_energy.install into compile.py only',
        inputs=records, generated_compiler_sha256=sha(compiler),
        ATR_sha256=sha(out / 'candidate.atr')), indent=2) + '\n')


if __name__ == '__main__':
    main()
