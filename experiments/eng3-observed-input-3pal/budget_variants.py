"""Measure offline proposals A/B before compiling a resident candidate."""
from pathlib import Path
import concurrent.futures,os,subprocess,json,shutil,struct
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal');OLD=Path('build/art2-neon-palettes')
def sections(p):
 b=p.read_bytes();return {a:b[144+o:144+o+n] for a,n,o,c in [struct.unpack_from('<4H',b,16+i*8) for i in range(b[6])]}
def one(job):
 variant,area,fixture=job;out=B/'proposals'/variant/f'area-{area}'/fixture;out.mkdir(parents=True,exist_ok=True);shutil.copytree(S/'reference',out/'reference',dirs_exist_ok=True)
 env=dict(os.environ,NEON_ART2_BUILD=str(out),NEON_ART2_AREA=str(area),NEON_ART2_FIXTURE=fixture,ART3_VARIANT=variant)
 with (out/'compile.log').open('w') as log:r=subprocess.run(['python3',str(S/'compile.py')],env=env,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:print(job,'FAIL',flush=True);return dict(job=job,status='FAIL',log=str(out/'compile.log'))
 result=[]
 for scene in range(3):
  old=OLD/f'area-{area}'/('open' if fixture=='open' else '');a=sections(old/f'scene-{scene}.nrq');b=sections(out/f'scene-{scene}.nrq');banks=[]
  alloc=json.loads((out/f'scene-{scene}-banks.json').read_text())
  for i,addr in enumerate([0x8c00,0xa000,0xa400,0xa800,0xac00]):
   x=[a[addr][j:j+8] for j in range(0,992,8)];y=[b[addr][j:j+8] for j in range(0,992,8)]
   banks.append(dict(bank=i,new_patterns=len(set(y)-set(x)),retired_patterns=len(set(x)-set(y)),changed_slots=sum(v!=w for v,w in zip(x,y)),static_unique=alloc['banks'][i]['static_unique'],reserved=4,free=alloc['banks'][i]['free']))
  d=a[0x9de0];e=b[0x9de0];assert d[:4]==e[:4] and d[536:]==e[536:];assert a[0xb160]==b[0xb160]
  oldanim=[struct.unpack_from('<HBB4B',d,128+j*8)[1:3] for j in range(d[4])];newanim=[struct.unpack_from('<HBB4B',e,128+j*8)[1:3] for j in range(e[4])];assert oldanim==newanim,(job,scene,oldanim,newanim)
  result.append(dict(scene=scene,banks=banks,animation_records=e[4],RAW=sum(map(len,b.values())),disk=(out/f'scene-{scene}.nrq').stat().st_size,decorations=json.loads((out/f'scene-{scene}-decoration.json').read_text())))
 print(job,'PASS',min(b['free'] for s in result for b in s['banks']),flush=True)
 return dict(job=job,status='PASS',scenes=result,resident_growth='estimated0: only offline selection',RAM_growth='0: exact same section extents',buffers=0,per_frame_extra_work='0: no new routines or descriptors')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(one,[(v,a,f) for v in ['A','B'] for a in range(1,5) for f in ['obstacles','open']]))
(B/'proposal-measurements.json').write_text(json.dumps(r,indent=2)+'\n')
assert all(v['status']=='PASS' for v in r)
