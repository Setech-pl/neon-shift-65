"""Rebuild every fixture from the portable, immutable source archive."""
from capture_cases import *
root=B/'archive-reproduction';root.mkdir()
with tarfile.open(D/'source-freeze.tar.gz') as t:t.extractall(root,filter='data')
binding=json.loads((D/'candidate-binding.json').read_text())
assert all(sha(root/p)==h for p,h in binding['sources'].items())
def one(job):
 a,f=job;out=root/f'build/area-{a}-{f}'
 env=dict(os.environ,NEON_ART2_AREA=str(a),NEON_ART2_BUILD=str(out),NEON_ART2_FIXTURE=f)
 log=root/f'area-{a}-{f}.log'
 with log.open('w') as stream:subprocess.run([sys.executable,'experiments/eng3-observed-input-3pal/build.py'],cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
 target=D.parent/f'area-{a}'/('open' if f=='open' else '')
 compared=[dict(name=p.name,expected=sha(target/p.name),actual=sha(p)) for p in sorted(out.glob('*.atr'))]
 assert len(compared)==8 and all(q['expected']==q['actual'] for q in compared)
 print(a,f,'archive8ATRidentical',flush=True);return dict(area=a,fixture=f,ATR=compared,ASan_UBSan_sim65='PASS actual execution',log=str(log.relative_to(R)))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,[(a,f) for a in range(1,5) for f in ['obstacles','open']]))
js(D/'archive-rebuild.json',dict(status='PASS',source_archive_sha256=sha(D/'source-freeze.tar.gz'),clean_builds=8,ATR_comparisons=64,source_count=len(binding['sources']),results=results))
