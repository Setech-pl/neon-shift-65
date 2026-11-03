#!/usr/bin/env python3
"""Verify exact disk, four scores, 60 scenes and RAM budgets; no solver audit."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('--reference-build',type=Path);a=p.parse_args();b=a.build
expected='72f1d0643c562937312d71beeaa7965cda5fd5213b9e3891f292bf55f12dc477'
disk=(b/'candidate.atr').read_bytes();assert len(disk)==1048592 and hashlib.sha256(disk).hexdigest()==expected
scores=[(b/f'music-{i}.nrq').read_bytes() for i in range(1,5)];assert len(set(scores))==4
assert len(json.loads((Path(__file__).resolve().parents[1]/'assets/levels/camp2-b/campaign.json').read_text())['levels'])==60
seg={n:(int(start,16),int(size,16)) for n,start,end,size,align in re.findall(r'^([A-Z_0-9]+)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{5})$',(b/'candidate.map').read_text(),re.M)}
free={n:limit-sum(seg[n]) for n,limit in dict(BSS=0x8000,LOADBSS=0x1400,ZEROPAGE=0x100,PERSIST=0x9800,EXTRA=0x2000).items()};assert min(free.values())>=0;assert seg['CSTACK'][1]==2048
if a.reference_build:
 ref=a.reference_build
 for f in b.glob('*.nrq'):assert f.read_bytes()==(ref/f.name).read_bytes(),f.name
 for f in (b/'source').iterdir():
  if f.suffix in ('.c','.h','.s','.cfg'):assert f.read_bytes().replace(str(b.resolve()).encode(),b'BUILD')==(ref/'source'/f.name).read_bytes().replace(str(ref.resolve()).encode(),b'BUILD'),f.name
 assert (b/'candidate.map').read_bytes().replace(str(b.resolve()).encode(),b'BUILD')==(ref/'candidate.map').read_bytes().replace(str(ref.resolve()).encode(),b'BUILD')
print(json.dumps(dict(status='PASS',ATR_sha256=expected,levels=60,scores=4,RAM_free=free,C_stack=2048,hardware_stack=256,identical_generated_code_assets_and_map=bool(a.reference_build)),indent=2))
