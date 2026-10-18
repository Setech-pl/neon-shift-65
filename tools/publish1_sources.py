#!/usr/bin/env python3
"""Materialize pinned production inputs for a fresh build; no old build cache."""
import argparse,json,subprocess,hashlib
from pathlib import Path
from publish1_prepare import ROOT,PRODUCT,blob

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    lock=json.loads((ROOT/'docs/publish1/source-inputs.json').read_text())
    for name,expected in lock['inputs'].items():
        try:data=blob(name)
        except subprocess.CalledProcessError:data=(ROOT/name).read_bytes()
        assert hashlib.sha256(data).hexdigest()==expected,name
        dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    print(out)
if __name__=='__main__':main()
