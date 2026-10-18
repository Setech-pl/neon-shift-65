"""External edges immediately on both sides of measured device query boundaries."""
from capture_cases import *
def one(job):
 a,q,boundary,side=job;out=run(a,'query-boundaries',q);result=json.loads((out/'result.json').read_text());compress(out)
 return dict(area=a,job=q,boundary_clock=boundary,side=side,external_t0=q[2],result=result,raw=str(out.relative_to(R)))
d=json.loads((D/'capture-128-final.json').read_text())['records'];jobs=[]
for a in range(1,5):
 for name in ['RZ-phase039','RZ-phase128','RZ-phase248','RZ-phase200']:
  r=next(r for r in d if r['area']==a and r['id']==name);boundary=r['edge_bounds_from_actual_device_queries']['direction'][0]
  for side in [-1,1]:
   q=r['job'].copy();q[0]=f'{name}-query-{side:+d}';q[2]=boundary+side;jobs.append((a,q,boundary,side))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,jobs))
js(D/'query-boundaries.json',dict(scope='32 fresh physical schedules; external t0 is known fixed query-boundary±1, gap217 unchanged. Subsequent query time may move when early input changes execution; both schedules and actual query logs retained. Not a global minimum-gap qualification.',runs=result))
print('query boundaries',len(result))
