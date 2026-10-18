"""Bounded decoration qualification; logs never reinterpret ENGINE as PASS."""
import concurrent.futures,json,subprocess,sys
from pathlib import Path
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal');mode=sys.argv[1]
def run(job):
 a,f,task=job;out=B/f'area-{a}'/('open' if f=='open' else '');out.mkdir(exist_ok=True)
 if task in ['atlas','connections','loader']:cmd=[sys.executable,str(S/'auxiliary.py'),str(a),task]
 elif task=='export':cmd=[sys.executable,str(S/'export_pack.py'),str(a)]
 elif task=='dock':cmd=[sys.executable,str(S/'qualify.py'),str(a),f,'dock']
 else:cmd=[sys.executable,str(S/'qualify.py'),str(a),f,'game',task]
 with (out/f'art3-{task}.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 print(a,f,task,r.returncode,flush=True);return dict(area=a,fixture=f,task=task,exit=r.returncode,command=cmd)
if mode=='oracle':jobs=[(a,f,'oracle') for a in range(1,5) for f in ['obstacles','open']]
elif mode=='game':jobs=[(a,f,t) for a in range(1,5) for f in ['obstacles','open'] for t in (['replay','hud','repeat','small-ui','attract'] if f=='obstacles' else ['replay'])]
elif mode=='dock':jobs=[(a,'obstacles','dock') for a in range(1,5)]
elif mode=='export':jobs=[(a,'obstacles','export') for a in range(1,5)]
elif mode=='media':jobs=[(a,'obstacles',t) for a in range(1,5) for t in ['atlas','connections','loader']]
else:raise ValueError(mode)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(run,jobs))
(B/f'art3-{mode}-matrix.json').write_text(json.dumps(result,indent=2)+'\n')
assert not any(r['exit'] for r in result),result
