"""Reproduce all 128 ENG1 mismatches and test indistinguishable opposite histories.

No input information is passed to the Atari program except standard pins.
The host derives a second schedule from actual query constraints for measurement.
"""
from pathlib import Path
import csv,json,hashlib,os,subprocess,sys,concurrent.futures,tarfile,io
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent
B=R/'build/eng3-observed-input-3pal';D=R/'docs/checkpoints/eng3-observed-input-3pal/evidence'
OLD=R/'build/eng1-action-semantics-and-campaign-memory-v5'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [{k:(v if k=='gs_hex' else int(v)) for k,v in r.items()} for r in csv.DictReader(p.open())]
def js(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def compress(out):
 files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='raw.tar.gz')
 manifest={str(p.relative_to(out)):sha(p) for p in files}
 with tarfile.open(out/'raw.tar.gz','w:gz',compresslevel=6) as t:
  for p in files:t.add(p,arcname=str(p.relative_to(out)),recursive=False)
 # Lossless archive retains every raw file. Keep small/readable evidence expanded.
 for p in files:
  if p.suffix not in ('.json','.log','.cfg') and p.name not in ('pins.csv','device-reads.csv','fixed-pin-events.csv','requested.json'):p.unlink()
 js(out/'raw-manifest.json',dict(files=manifest,archive_sha256=sha(out/'raw.tar.gz'),restore='tar -xzf raw.tar.gz in this output directory; all original bytes retained'))
def run(a,kind,q,release=None):
 out=B/f'area-{a}'/kind/q[0];env=dict(os.environ,A5C_RUN_ROOT=str(out.parent.relative_to(R)),NEON_A5C_BUDGET_OBSERVER=str(B/'observer/src/atari800'),ENG2_BUS_RANGE='1140,1142',NSQ_BUDGET='1140,1142')
 if release is not None:env['A5C_RELEASE_CLOCK']=str(release)
 out.parent.mkdir(parents=True,exist_ok=True)
 with (out.parent/(q[0]+'.log')).open('w') as log:
  p=subprocess.run([sys.executable,str(S/'qualify.py'),str(a),'obstacles','physical','--one',json.dumps(q)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert p.returncode==0,(q,out.parent/(q[0]+'.log'))
 return out
def transcript(out):
 # Pins in the host observer are deliberately excluded: not target information.
 keys=['frame','clock','ypos','xpos','pc','opcode','arg','a','x','y','s']+[f'm{i}' for i in range(12)]
 h=hashlib.sha256()
 if (out/'input-instructions.csv').exists():f=(out/'input-instructions.csv').open()
 else:
  archive=tarfile.open(out/'raw.tar.gz');f=io.TextIOWrapper(archive.extractfile('input-instructions.csv'))
 for r in csv.DictReader(f):h.update((','.join(r[k] for k in keys)+'\n').encode())
 f.close()
 return h.hexdigest()
def one(job):
 cached=B/f'area-{job[0]}'/'capture-original'/job[2][0]/'capture-classification.json'
 if cached.exists() and (cached.parent/'raw-manifest.json').exists():return json.loads(cached.read_text())
 a,kind,q=job;old=OLD/f'area-{a}'/kind/q[0];orig=json.loads((old/'result.json').read_text());out=run(a,'capture-original',q)
 d=json.loads((out/'result.json').read_text());bus=rows(out/'device-reads.csv');pin=d['external_events'];t0,t1=pin[0][0],pin[1][0]
 assert d['actions']==orig['actions'] and d['images']==orig['images'],('instrumentation changed target behavior',a,q)
 assert all(r['gractl']&4==0 and r['pactl']&4 and r['ddra_mask']&15==15 for r in bus)
 direction=q[1].replace('Z','');values={'R':7,'U':14,'D':13,'L':11}
 bounds={}
 for name,addr,neutral,active in [('direction',0xd300,15,values[direction]),('fire',0xd010,1,0)]:
  rr=[r for r in bus if r['address']==addr and r['clock']<pin[2][0]]
  first=next(r for r in rr if r['clock']>=t0 and r['value']&(15 if name=='direction' else 1)==active)
  previous=max((r['clock'] for r in rr if r['clock']<first['clock'] and r['value']&(15 if name=='direction' else 1)==neutral),default=40511952)
  bounds[name]=[previous,first['clock']-1]
 # Opposite order with the SAME 217-clock physical gap whenever constraints allow.
 reversed_pattern=q[1][::-1];first_name='fire' if reversed_pattern[0]=='Z' else 'direction';second_name='direction' if first_name=='fire' else 'fire'
 lo=max(bounds[first_name][0]+1,bounds[second_name][0]+1-q[3]);hi=min(bounds[first_name][1]-1,bounds[second_name][1]-1-q[3])
 pair=None
 if lo<=hi:
  start=(lo+hi)//2
  pq=[q[0]+'-opposite',reversed_pattern,start,q[3],q[4],q[5]]
  other=run(a,'capture-opposite',pq,pin[2][0]);od=json.loads((other/'result.json').read_text())
  equal_bus=(out/'device-reads.csv').read_bytes()==(other/'device-reads.csv').read_bytes()
  same_transcript=transcript(out)==transcript(other)
  same_actions=d['actions']==od['actions']
  frame_equal={str(f):(out/f'native-{f:04}.png').read_bytes()==(other/f'native-{f:04}.png').read_bytes() for f in range(1139,1149)}
  pair=dict(external_events=od['external_events'],raw=str(other.relative_to(R)),device_reads_identical=equal_bus,CPU_and_protocol_transcript_identical=same_transcript,actual_actions_identical=same_actions,native_frames_identical=frame_equal,transcript_hash=transcript(other),scope='Current sampler and Atari800 modeled bus; no universal optimal-sampler impossibility claim')
  assert equal_bus and same_transcript and same_actions and all(frame_equal.values()),(a,q,'counterfactual not identical')
  compress(other)
 nearby=[r for r in bus if t0-1000<=r['clock']<=t1+1000]
 observed=[r for r in bus if t0<r['clock']<t1]
 result=dict(area=a,id=q[0],ENG1_kind=kind,job=q,raw=str(out.relative_to(R)),external_events=pin,classification='B_CAPTURE_GAP',secondary='C_EQUIVALENT_TRANSCRIPT_CURRENT_PATH' if pair else 'OPPOSITE_TRANSCRIPT_NOT_YET_PROVEN',physical_requested=q[1],actual_order=''.join(x['action'] for x in d['actions']),program_available_intermediate_reads=observed,edge_bounds_from_actual_device_queries=bounds,nearby_reads=nearby,actions=d['actions'],displayed_images=d['images'],final_state=d['final'],opposite_pair=pair,baseline_actions_and_images_identical=True,transcript_hash=transcript(out),qualification='FAIL requested physical chronology; ambiguity is not PASS')
 js(out/'capture-classification.json',result);compress(out)
 print(a,q[0],result['classification'],bool(pair),flush=True)
 return result
if __name__=='__main__':
 availability=json.loads((R/'docs/checkpoints/eng1-action-semantics-and-campaign-memory/evidence/remaining-order-availability-v5.json').read_text());jobs=[]
 for r in availability:
  path=Path(r['case']);a=int(path.parts[-3].split('-')[-1]);kind=path.parts[-2];name=path.name
  q=next(q for q in json.loads((OLD/f'area-{a}'/kind/'jobs.json').read_text()) if q[0]==name)
  jobs.append((a,kind,q))
 assert len(jobs)==128
 if '--one' in sys.argv:result=[one(jobs[int(sys.argv[-1])])]
 else:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,jobs))
 js(D/'capture-128.json',dict(cases=len(result),records=result))
