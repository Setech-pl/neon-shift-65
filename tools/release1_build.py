#!/usr/bin/env python3
"""Materialize identified inputs, then build five ATRs and a second clean menu ATR."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'build/release1';manifest=json.loads((ROOT/'docs/finish2/manifest.json').read_text())['source_dependency_inventory']
    paths=set(manifest)|{str(p.relative_to(ROOT)) for p in (ROOT/'tools').glob('release1_*.py')}|{'experiments/release1/art.py'}
    # Source-bound snapshot, excluding all old build products and captures.
    bindings={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)}
    state=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),inputs=bindings)
    (ROOT/'docs/release1/build-inputs.json').write_text(json.dumps(state,indent=2)+'\n')
    for name in ('source-a','source-b'):
        tree=out/name;tree.mkdir(exist_ok=False)
        for p in sorted(paths):
            dest=tree/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,dest)
        assert all(hashlib.sha256((tree/p).read_bytes()).hexdigest()==h for p,h in bindings.items())
    for folder,n in [('final',None)]+[(f'test-{n}',n) for n in (1,16,31,46)]+[('rebuild',None)]:
        tree=out/('source-b' if folder=='rebuild' else 'source-a')
        cmd=[sys.executable,'tools/v1_build.py','--out',str(out/folder)]
        if n:cmd+=['--test-start',str(n)]
        subprocess.run(cmd,cwd=tree,check=True)
    assert (out/'final/candidate.atr').read_bytes()==(out/'rebuild/candidate.atr').read_bytes()
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in bindings.items())
    print('PASS five isolated builds; two clean menu builds byte-identical')

if __name__=='__main__':main()
