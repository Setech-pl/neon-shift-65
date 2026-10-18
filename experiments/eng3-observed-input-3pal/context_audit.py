"""Independent spatial constraints on generated plans; wall boundary contract."""
import os,json,subprocess,sys
from pathlib import Path
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal')
if len(sys.argv)>1:
 sys.path.insert(0,str(S.resolve()));import compile as c
 # Verify every canonical wall variant against baseline themed functions.
 import inspect
 original=c.wall;c.wall=inspect.getclosurevars(original).nonlocals['original']
 for mask in range(16):
  for kind in [0,1]:
   a=c.decode_tile(c.wall(mask,0 if mask in (5,10) else kind));b=c.decode_tile(original(mask,kind))
   for y in range(16):
    for x in range(8):
     if y in [0,15] or x in [0,7]:assert a[y][x]==b[y][x],(mask,kind,x,y)
 print('PASS all32 canonical wall boundaries');raise SystemExit
records=[]
for a in range(1,5):
 env=dict(os.environ,NEON_ART2_AREA=str(a));subprocess.run([sys.executable,__file__,'walls'],env=env,check=True)
 for fixture in ['', 'open']:
  root=B/f'area-{a}'/fixture;levels=json.loads((root/'levels.json').read_text())['levels']
  for i,l in enumerate(levels):
   d=json.loads((root/f'scene-{i}-decoration.json').read_text());rows=l['rows'];docks=[(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '.*+'];points={(v['x'],v['y']) for v in d['floor_selection']}
   for x,y in points:
    assert rows[y][x]!='#' and all(abs(x-u)+abs(y-v)>1 for u,v in docks)
    assert sum(0<=y+v<len(rows) and 0<=x+u<len(rows[0]) and rows[y+v][x+u]!='#' for u,v in [(0,1),(0,-1),(1,0),(-1,0)])>=3
    assert any(abs(x-u)+abs(y-v)==1 for u,v in points),(a,fixture,i,x,y,'isolated detail')
   alloc=json.loads((root/f'scene-{i}-banks.json').read_text());assert not alloc['conflicts']
   records.append(dict(area=a,fixture=fixture or 'obstacles',scene=i,variant=d['variant'],floor_details=len(points),anchors=d['anchors'],clear_docks_and_neighbours=True,narrow_passages_clear=True,all_details_in_small_clusters=True,bank_conflicts=0))
(B/'context-audit.json').write_text(json.dumps(dict(status='PASS',cases=records,wall_boundary_variants=128),indent=2)+'\n')
