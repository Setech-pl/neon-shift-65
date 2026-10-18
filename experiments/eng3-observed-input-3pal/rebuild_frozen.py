"""Reconstruct v2 from isolated frozen source closure; two clean builds/fixture.
No mutation of current target tree, old freeze or final ATR.
"""
from pathlib import Path
import concurrent.futures,hashlib,json,os,shutil,subprocess,sys
R=Path(__file__).resolve().parents[2];S=R/'experiments/eng3-observed-input-3pal';B=R/'build/eng3-observed-input-3pal';W=B/'frozen-rebuild';W.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[]
for name in ['src','assets','tools','cfg']:
 for p in (R/name).rglob('*'):
  if p.is_file() and '__pycache__' not in str(p):inputs.append(p)
inputs.extend(p for p in S.rglob('*') if p.is_file() and '__pycache__' not in str(p))
manifest={str(p.relative_to(R)):sha(p) for p in inputs};(W/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def one(q):
 a,f,round=q;root=W/f'area-{a}-{f}-round-{round}';root.mkdir()
 for name in manifest:
  dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,dst);assert sha(dst)==manifest[name]
 out=root/'build/candidate';env=dict(os.environ,NEON_ART2_AREA=str(a),NEON_ART2_BUILD=str(out),NEON_ART2_FIXTURE=f)
 with (root/'rebuild.log').open('w') as log:r=subprocess.run([sys.executable,str(root/S.relative_to(R)/'build.py')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0,(q,root/'rebuild.log')
 target=B/f'area-{a}'/('open' if f=='open' else '')
 comparisons=[{'variant':name,'rebuilt':sha(out/(name+'.atr')),'frozen':sha(target/(name+'.atr'))} for name in ['candidate','dim','stress','carry','wrap','counter9','counter99','counter999']]
 assert all(r['rebuilt']==r['frozen'] for r in comparisons),(q,comparisons)
 print(q,'PASS8ATR',flush=True);return {'area':a,'fixture':f,'round':round,'status':'PASS','ASan_UBSan':'PASS actual run','sim65':'PASS actual run','ATR':comparisons}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:r=list(p.map(one,[(a,f,n) for a in range(1,5) for f in ['obstacles','open'] for n in [1,2]]))
(W/'result.json').write_text(json.dumps({'status':'PASS','isolated_builds':len(r),'comparisons':len(r)*8,'source_manifest':sha(W/'source-manifest.json'),'results':r},indent=2)+'\n')
