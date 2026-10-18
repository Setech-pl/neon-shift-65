"""Repeat frozen external-t0 engine fixtures independently for every area."""
import concurrent.futures,json,subprocess,sys,os
from pathlib import Path
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal');mode=sys.argv[1]
def invoke(q):
 area,kind,value=q;root=B/f'area-{area}';dest=root/kind;dest.mkdir(exist_ok=True)
 if kind=='phase-accepted':
  k,p=value;name=f'own53-ENG1-{k}-{p:03}';args=['phase','--one','ENG1',k,str(p)]
 else:
  name=value[0];args=['physical','--one',json.dumps(value)]
 env=dict(os.environ,NEON_A5C_BUILD=str(root),A5C_RUN_ROOT=str(dest),NEON_A5C_BUDGET_OBSERVER=str(Path('build/ux1-menu-splash-loader-crates-review/observer-v2/src/atari800').resolve()),NSQ_BUDGET='1140,1142')
 with (dest/(name+'.log')).open('w') as log:r=subprocess.run([sys.executable,str(S/'qualify.py'),str(area),'obstacles',*args],env=env,stdout=log,stderr=subprocess.STDOUT)
 print(area,kind,name,r.returncode,flush=True);return dict(area=area,kind=kind,name=name,exit=r.returncode)
jobs=[]
if mode=='engine':
 for a in range(1,5):
  for kind in ['engine-accepted','engine-extra']:
   values=json.loads(Path(f'build/ux2-early-splash-and-loading-screen/{kind}/jobs.json').read_text())
   root=B/f'area-{a}'/kind;root.mkdir(exist_ok=True);(root/'jobs.json').write_text(json.dumps(values,indent=2)+'\n')
   jobs.extend((a,kind,v) for v in values)
elif mode=='phase':
 phases=sorted(set(range(0,312,16))|set(range(39,51))|set(range(198,204))|set(range(247,250))|{311}|set(range(20,27))|set(range(258,263)))
 jobs=[(a,'phase-accepted',(k,p)) for a in range(1,5) for p in phases for k in ['push','undo']]
else:raise ValueError(mode)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(invoke,jobs))
(B/(mode+'-runs.json')).write_text(json.dumps(results,indent=2)+'\n')
assert not any(q['exit'] for q in results),[q for q in results if q['exit']]
