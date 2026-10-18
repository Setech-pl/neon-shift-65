#!/usr/bin/env python3
"""Materialize current locked inputs, without Git objects or inherited outputs."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    lock=json.loads((ROOT/'docs/hwvis1/source-inputs.json').read_text())
    a.out.mkdir(parents=True,exist_ok=False)
    for name,digest in lock['inputs'].items():
        data=(ROOT/name).read_bytes();assert hashlib.sha256(data).hexdigest()==digest,name
        dest=a.out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    print(a.out)
if __name__=='__main__':main()
