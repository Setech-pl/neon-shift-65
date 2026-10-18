#!/usr/bin/env python3
"""Qualify the packed PRODUCT1 ATR with device-only cold-boot replays."""
import argparse,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'experiments/renderer-a5c'),str(ROOT/'tools')]
import gauntlet,verify,turbo_run
from product1_campaign import canonical
from solver import DIRS,parse,solve_path

def setup(B):
    gauntlet.ROOT=B
    os.environ.update(NEON_A5B_OBSERVER=str((ROOT/'build/eng3-observed-input-3pal/observer/src/atari800').resolve()),NEON_ATARI_CONFIG=str((ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg').resolve()))
    return verify.labels(B/'candidate.lbl')

def campaign(B,name):
    l=setup(B);levels=json.loads((ROOT/'assets/levels/product1-campaign.json').read_text())['levels']
    events=[(700,700,dict(fire=0))];captures=[650];records=[];f=1000;keys=set()
    for i,level in enumerate(levels):
        key=canonical(level['rows']);assert key not in keys;keys.add(key)
        path,states=solve_path('\n'.join(level['rows']),max_states=200000);assert path==level['path']
        captures.append(f-5)
        walls,targets,boxes,p,_,_=parse('\n'.join(level['rows']));pushes=0
        for c in path:
            events.append((f,f,dict(stick={'U':14,'D':13,'L':11,'R':7}[c])))
            dx,dy=DIRS[c];q=p[0]+dx,p[1]+dy
            if q in boxes:boxes.remove(q);boxes.add((q[0]+dx,q[1]+dy));pushes+=1
            p=q;f+=8
        assert boxes==targets
        captures.append(f+10);records.append(dict(level=i+1,frame=f+10,path=path,player=list(p),boxes=sorted(map(list,boxes)),moves=len(path),pushes=pushes,solver_states=states,canonical=key))
        events.append((f+20,f+20,dict(fire=0)));f+=320
    captures.append(f-10)
    events.extend([(f+2,f+2,dict(fire=0)),(f+350,f+350,dict(stick=13)),(f+370,f+370,dict(fire=0))]);captures.append(f+700)
    out=gauntlet.probe(name,events,captures,f+720,boot=True)
    for r in records:
        s=verify.state(out/f"frame-{r['frame']:04}.ram",l)
        assert s['phase']==2 and s['scene']==r['level']-1 and s['error']==0,(r,s)
        assert s['moves']==r['moves'] and s['pushes']==r['pushes'] and s['player']==r['player'] and sorted(s['boxes'])==r['boxes'],(r,s)
        assert s['overflow']==0 and s['publication_overflow']==0
        r['runtime']=s;r['status']='PASS'
    final=verify.state(out/f'frame-{f-10:04}.ram',l);assert final['phase']==10,final
    assert verify.state(out/f'frame-{f+700:04}.ram',l)['phase']==10
    # The emulator wrote only sectors in its copied ATR, using target OS SIO.
    disk=(out/'candidate.atr').read_bytes();original=(B/'candidate.atr').read_bytes()
    changed=[i for i,(a,b) in enumerate(zip(disk,original)) if a!=b]
    assert changed and all(16+(8100-1)*128<=i<16+8101*128 for i in changed)
    result=dict(status='PASS',ATR_sha256=hashlib.sha256(original).hexdigest(),levels=records,final=final,completed_session_continue='PASS returns to finale',total_pal_frames=f+720,changed_disk_bytes=len(changed),save_sectors=[8100,8101],hardware='NOT_RUN',visual='OWNER_PENDING')
    (out/'campaign-result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS full campaign + 60 solver/native runtime replays',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--name',default='campaign-run-r2');a=p.parse_args();campaign(Path(a.build),a.name)
if __name__=='__main__':main()
