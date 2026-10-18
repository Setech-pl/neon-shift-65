"""Build/qualify four active packs; host parallelism never changes PAL clocks."""
import os,sys,json,subprocess,concurrent.futures
from pathlib import Path
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal')
mode=sys.argv[1]
def run(job):
 area,fixture,task=job;out=B/f'area-{area}'/('open' if fixture=='open' else '');out.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,NEON_ART2_AREA=str(area),NEON_ART2_BUILD=str(out),NEON_ART2_FIXTURE=fixture)
 argv=[sys.executable,str(S/'build.py')] if task=='build' else [sys.executable,str(S/'qualify.py'),str(area),fixture,'game',task]
 with (out/(task+'.log')).open('w') as f:r=subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT)
 print(area,fixture,task,r.returncode,flush=True)
 return dict(area=area,fixture=fixture,task=task,exit=r.returncode,command=argv)
if mode=='build':jobs=[(a,f,'build') for a in range(1,5) for f in ('obstacles','open')]
elif mode=='game':
 for a in range(1,5):assert run((a,'obstacles','oracle'))['exit']==0
 jobs=[(a,'obstacles',t) for a in range(1,5) for t in ('replay','hud','repeat','small-ui','attract')]
else:raise ValueError(mode)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:result=list(p.map(run,jobs))
(B/(mode+'-matrix.json')).write_text(json.dumps(result,indent=2)+'\n')
assert not any(q['exit'] for q in result),[q for q in result if q['exit']]
