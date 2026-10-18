#!/usr/bin/env python3
"""Validate the short hardware routes and A-01 at the actual campaign finale."""
import json
from pathlib import Path
import release1_runtime as r
from release1_owner_smoke import route_disk
import release1_fire as fire

def main():
    media=r.BASE/'hardware-routes';media.mkdir(exist_ok=True);records=[]
    for n in (15,30,45,60):
        p=media/f'smoke-level-{n:02}.atr';info=route_disk(n,r.B/'candidate.atr',p);c=info['last_move']
        ev=[(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0)),(4700,4700,dict(stick=r.STICK[c])),(4800,4800,dict(fire=0))]
        out,s,l=r.probe('hardware-route-'+str(n),ev,[4600,4750,5500],5520,image=p.read_bytes(),stock=True)
        assert s[4600]['phase']==1 and s[4600]['scene']==n-1 and s[4600]['undo']==0
        assert s[4750]['phase']==2 and s[4750]['moves']==len(r.L[n-1]['path'])
        assert s[5500]['phase']==(10 if n==60 else 1) and s[5500]['scene']==(59 if n==60 else n)
        if n==60:
            _,cold,_=r.probe('cold-completed',[(700,700,dict(stick=13)),(730,730,dict(fire=0))],[1300],1320,image=(out/'candidate.atr').read_bytes());assert cold[1300]['phase']==10
            initial=r.L[59]['path'][:-1]
            q=fire.run(r.B,'finale-fire-proof',r.STICK[c],proof=True,image=p.read_bytes(),initial=initial,index=59)
            assert q['final']['scene']==59 and q['final']['phase']==1 and q['final']['moves']==len(initial)
            records.append(q)
            for shift in (-600,-300,0,300,600):
                q=fire.run(r.B,'finale-sweep-'+str(shift+600),r.STICK[c],shift=shift,image=p.read_bytes(),initial=initial,index=59)
                assert q['final']['scene']==59 and q['final']['phase']==1 and q['final']['moves']==len(initial)
                records.append(q)
        records.append(info)
    r.dump(Path('docs/release1/hardware-routes.json'),dict(status='PASS',tests=records,stock_route_tests=r.RESULTS))

if __name__=='__main__':main()
