"""Fresh ENG3-B-v1 matrix; original job IDs and physical t0 stay unchanged."""
from pathlib import Path
import os,sys,json,subprocess,concurrent.futures,hashlib
from capture_cases import compress
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent
B=R/'build/eng3-observed-input-3pal';D=R/'docs/checkpoints/eng3-observed-input-3pal/evidence'

def run(job):
    area,kind,q,waveform=job;root=B/f'area-{area}';out=root/kind/q[0]
    if (out/'raw-manifest.json').exists():return dict(area=area,kind=kind,id=q[0],result=str(out/'result.json'))
    out.parent.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,NEON_A5C_BUILD=str(root.relative_to(R)),A5C_RUN_ROOT=str(out.parent.relative_to(R)))
    if waveform:env['ENG3_WAVEFORM_JSON']=json.dumps(waveform)
    with (out.parent/(q[0]+'.log')).open('w') as f:
        p=subprocess.run([sys.executable,str(S/'physical.py'),'--one',json.dumps(q)],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
    if p.returncode:return dict(area=area,kind=kind,id=q[0],exit=p.returncode,log=str(out.parent/(q[0]+'.log')))
    compress(out)
    d=json.loads((out/'result.json').read_text())
    return dict(area=area,kind=kind,id=q[0],status=d['status'],gates=d['gates'],result=str(out/'result.json'))

def jobs(mode):
    if mode=='matrix':
        for area in range(1,5):
            for kind in ['engine-accepted','engine-extra']:
                src=R/f'build/eng2-capture-publication-feasibility/area-{area}/{kind}/jobs.json'
                values=json.loads(src.read_text());dest=B/f'area-{area}'/kind;dest.mkdir(exist_ok=True)
                (dest/'jobs.json').write_text(json.dumps(values,indent=2)+'\n')
                for q in values:yield area,kind,q,None
    elif mode=='pairs':
        history=json.loads((R/'docs/checkpoints/eng2-capture-publication-feasibility/evidence/capture-128-qualified.json').read_text())
        for r in history['records']:
            wave=(r['opposite_pair'] or r['supplemental_opposite_pair'])['external_events'];q=r['job'].copy()
            q[0]+='-historical-opposite';q[1]=q[1][::-1];q[2]=wave[0][0];q[3]=wave[1][0]-wave[0][0]
            yield r['area'],'historical-pairs',q,wave
    elif mode=='new':
        for area in range(1,5):
            for variant in ['candidate','carry']:
                for phase in [0,42,152,192,247,310,311]:
                    t0=40511952+phase*114+12
                    for name,wave,prefix in [
                        ('tie-RZS',[[t0,7,0,6],[t0+35568,15,1,7]],''),
                        ('tie-RZ',[[t0,7,0,7],[t0+35568,15,1,7]],''),
                        ('tie-UZS-nohistory',[[t0,14,0,6],[t0+35568,15,1,7]],''),
                        ('resolved-R-Z-S',[[t0,7,1,7],[t0+35568,15,0,7],[t0+2*35568,15,1,6],[t0+3*35568,15,1,7]],''),
                        ('resolved-Z-R-S',[[t0,15,0,7],[t0+35568,7,1,7],[t0+2*35568,15,1,6],[t0+3*35568,15,1,7]],'R' if variant=='carry' else '')]:
                        q=[f'{variant}-{name}-phase{phase:03}','RZ',t0,0,prefix,variant]
                        yield area,'new-contract-v3' if name=='resolved-Z-R-S' and variant=='candidate' else 'new-contract',q,wave
    else:raise ValueError(mode)

if __name__=='__main__':
    mode=sys.argv[1];tasks=list(jobs(mode));records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,r in enumerate(pool.map(run,tasks)):
            records.append(r)
            if i%20==0 or 'exit' in r:print(mode,i+1,'/',len(tasks),r.get('status',r.get('exit')),flush=True)
    (D/(mode+'-runs.json')).write_text(json.dumps(dict(contract='ENG3-B-v1',runs=records),indent=2)+'\n')
    print(mode,'complete',len(records),'errors',sum('exit' in r for r in records),'FAIL',sum(r.get('status')=='FAIL' for r in records),flush=True)
    assert not any('exit' in r for r in records)
