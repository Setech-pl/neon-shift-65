#!/usr/bin/env python3
"""Build the normal NEON SHIFT 65 release disk."""
import argparse, hashlib, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',default='build/release')
a=p.parse_args()
subprocess.run([sys.executable,str(root/'tools/v1_build.py'),'--final-fix1','--out',a.out],cwd=root,check=True)
out=Path(a.out)
if not out.is_absolute():out=root/out
disk=out/'candidate.atr'
print('Normal ATR:',disk)
print('SHA-256:',hashlib.sha256(disk.read_bytes()).hexdigest())
