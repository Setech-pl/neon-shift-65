"""Freeze final target sources/64 ATR without rebinding any older checkpoint."""
from capture_cases import *
import shutil,re
CP=D.parent;frozen=B/'frozen-source';assert not frozen.exists();frozen.mkdir()
source={}
for name in ['src','assets','tools','cfg','experiments/eng3-observed-input-3pal']:
 for p in (R/name).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts:continue
  rel=p.relative_to(R);q=frozen/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);source[str(rel)]=sha(q)
artifacts={}
for a in range(1,5):
 for fixture in ['', 'open']:
  root=B/f'area-{a}'/fixture;target=CP/f'area-{a}'/fixture;target.mkdir(parents=True,exist_ok=True)
  for p in sorted(root.iterdir()):
   if not p.is_file() or p.suffix not in ('.atr','.xex','.lbl','.map','.nrq','.json'):continue
   if p.name.endswith('.atr') or p.name.startswith(('candidate.','carry.','dim.','stress.','wrap.','counter9.','counter99.','counter999.','scene-','levels.','solutions.','packages.','resource-measurements.','game-measurements.','qualification-summary.','ux2-contracts.')):
    q=target/p.name;shutil.copyfile(p,q);artifacts[str(q.relative_to(R))]=sha(q)
binding=dict(revision='ENG2-v1-diagnostic-freeze-byte-identical-ENG1-v5',base='75ef080f73abfc91ecd742efb2c85601e6246c30',source_root=str(frozen.relative_to(R)),sources=source,artifacts=artifacts,ATR={p:h for p,h in artifacts.items() if p.endswith('.atr')},runtime_changes='none: evidence does not justify a priority change or test-phase tuning',instrumentation='host observer only; runtime has no host/oracle channel')
assert len(binding['ATR'])==64
js(D/'candidate-binding.json',binding)
with tarfile.open(D/'source-freeze.tar.gz','w:gz',compresslevel=9) as t:
 for p in sorted(source):t.add(frozen/p,arcname=p,recursive=False)
js(D/'freeze-integrity.json',dict(binding_sha256=sha(D/'candidate-binding.json'),source_archive_sha256=sha(D/'source-freeze.tar.gz'),source_count=len(source),ATR_count=64))
print('Frozen',len(source),'sources,64ATR')
