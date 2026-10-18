"""Four clean rounds per area, alternating unchanged logical fixtures.

128 ATR comparisons: 4 areas x4 full builds x8 native variants. Both obstacle
and old open fixture are built twice. ASan/UBSan and sim65 run in every build.
"""
import concurrent.futures,os,json,hashlib,shutil,subprocess,tempfile
from pathlib import Path
S=Path('experiments/eng3-observed-input-3pal');B=Path('build/eng3-observed-input-3pal')
dst=Path(tempfile.mkdtemp(prefix='neon-art2-rebuild-',dir='/private/tmp'))
for d in ['src','assets','cfg','tools',str(S)]:
 shutil.copytree(d,dst/d,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def one(area):
 results=[]
 for i in range(4):
  fixture='open' if i%2 else 'obstacles';output=f'build/rebuild-area-{area}-{i}'
  env=dict(os.environ,NEON_ART2_BUILD=output,NEON_ART2_AREA=str(area),NEON_ART2_FIXTURE=fixture)
  with (dst/f'area-{area}-round-{i}.log').open('w') as log:subprocess.run(['python3',str(S/'build.py')],cwd=dst,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  ref=B/f'area-{area}'/('open' if fixture=='open' else '');checks=[]
  for name in ['candidate','dim','stress','carry','wrap','counter9','counter99','counter999']:
   expected=sha(ref/(name+'.atr'));got=sha(dst/output/(name+'.atr'));assert got==expected,(area,i,name,expected,got)
   checks.append(dict(variant=name,sha256=got))
  results.append(dict(area=area,round=i,fixture=fixture,checks=checks));print(area,i,fixture,'8/8 identical',flush=True)
 return results
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:results=[q for group in p.map(one,range(1,5)) for q in group]
(B/'rebuild.json').write_text(json.dumps(dict(status='PASS',isolated_directory=str(dst),full_builds=16,ATR_comparisons=128,ASAN_UBSAN_sim65='PASS each build',results=results),indent=2)+'\n')
