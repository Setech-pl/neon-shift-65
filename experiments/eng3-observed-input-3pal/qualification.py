"""Fresh ENG2 qualification; lossless raw archives keep disk use bounded."""
from pathlib import Path
import concurrent.futures,json,subprocess,os,sys,shutil
from capture_cases import compress,js,B,R,S,D,run
def invoke(args,env=None):
 cmd=[sys.executable,str(S/args[0]),*map(str,args[1:])]
 log=B/'logs'/('-'.join(map(str,args))+'.log');log.parent.mkdir(exist_ok=True)
 with log.open('w') as f:p=subprocess.run(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,(cmd,log)
 return dict(command=cmd,exit=p.returncode,log=str(log.relative_to(R)))
def engine(job):
 a,kind,q=job;copy=B/f'area-{a}'/kind/q[0]
 if (copy/'raw-manifest.json').exists():return dict(area=a,id=q[0],reused='completed fresh run')
 if copy.exists() and not list(copy.iterdir()):copy.rename(copy.with_name('adapter-precreated-'+q[0]))
 old=B/f'area-{a}'/'capture-original'/q[0]
 if (old/'capture-classification.json').exists():
  copy.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(old/'result.json',copy/'result.json');js(copy/'raw-reference.json',dict(raw=str(old.relative_to(R)),role='fresh ENG2 original waveform already rerun in capture128'))
  return dict(area=a,id=q[0],reused='fresh capture128')
 actual=run(a,kind,q);compress(actual)
 return dict(area=a,id=q[0],status='completed fresh independent actual-state/native oracle; requested-order and latency failures retained')
def phase(job):
 a,k,p=job;out=B/f'area-{a}'/'phase-accepted'/f'own53-ENG2-{k}-{p:03}'
 result=invoke(['qualify.py',a,'obstacles','phase','--one','ENG2',k,p]);compress(out);return result
def floor(job):
 a,f=job;result=invoke(['floor_qualification.py',a,f]);compress(B/'floors/final/floor-walk'/f'area-{a}-{f}');return result
def ux(a):
 scope={};exec((R/'experiments/ux2-early-splash-and-loading-screen/ux2_runs.py').read_text().split('def one')[0].replace('from probe import probe,B','probe=None;B=None'),scope)
 records=[invoke(['ux_qualification.py',a,'case',c]) for c in scope['CASES']]
 records.append(invoke(['ux_qualification.py',a,'analyze']))
 for out in (B/f'area-{a}').glob('accepted-*'):compress(out)
 return dict(area=a,runs=records)
def audio(a):
 record=invoke(['audio_video.py',a]);compress(B/f'area-{a}'/'native-film');return record
def focused(a):
 record=invoke(['focused.py',a]);return record
def measure(a):
 return dict(area=a,runs=[invoke(['qualify.py',a,'obstacles',k]) for k in ['dock','open-order','measure']])
if __name__=='__main__':
 mode=sys.argv[1];jobs=[]
 if mode=='engine':
  for a in range(1,5):
   for kind in ['engine-accepted','engine-extra']:
    src=R/'build/eng1-action-semantics-and-campaign-memory-v5'/f'area-{a}'/kind/'jobs.json'
    out=B/f'area-{a}'/kind;out.mkdir(exist_ok=True);shutil.copyfile(src,out/'jobs.json');jobs.extend((a,kind,q) for q in json.loads(src.read_text()))
  fun=engine;workers=3
 elif mode=='phase':
  phases=sorted(set(range(0,312,16))|set(range(39,51))|set(range(198,204))|set(range(247,250))|{311}|set(range(20,27))|set(range(258,263)))
  jobs=[(a,k,p) for a in range(1,5) for p in phases for k in ['push','undo']];fun=phase;workers=3
 elif mode=='floor':jobs=[(a,f) for a in range(1,5) for f in ['obstacles','open','maximum']];fun=floor;workers=2
 else:jobs=list(range(1,5));fun={'UX':ux,'audio':audio,'focused':focused,'measure':measure}[mode];workers=2
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  result=[]
  for i,r in enumerate(pool.map(fun,jobs)):
   result.append(r)
   if i%20==0:print(mode,i+1,'/',len(jobs),flush=True)
 js(D/f'{mode}-runs.json',dict(mode=mode,runs=result))
 print(mode,'complete',len(result))
