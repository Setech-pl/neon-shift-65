#!/usr/bin/env python3
"""Current ATR regressions, leaving historical RELEASE1 evidence untouched."""
import argparse,inspect,json,os
from pathlib import Path
import release1_runtime as r
from hwvis1_probe import configure
BASE=Path('build/hwvis1');DOC=Path('docs/hwvis1')
def main():
    a=argparse.ArgumentParser();a.add_argument('mode',choices=('campaign','saves','extra','transitions'));mode=a.parse_args().mode
    configure();r.BASE=BASE;r.B=BASE/'final'
    native=r.dump
    def dump(p,v):
        if str(p).startswith('docs/release1/'):p=DOC/Path(p).name
        native(p,v)
    r.dump=dump
    if mode=='campaign':
        source=inspect.getsource(r.campaign).replace('(700,700,dict(fire=0))','(3200,3200,dict(fire=0))').replace('f=1000','f=4600').replace('f+=330','f+=650').replace('build=b)','build=b,stock=True)')
        exec(source,r.__dict__);r.campaign(name='campaign-stock')
    elif mode=='saves':r.saves();r.errors();dump(DOC/'saves-tests.json',dict(status='PASS',tests=r.RESULTS))
    elif mode=='extra':
        from release1_extra import main
        main()
    else:
        from hwvis1_probe import probe
        from release1_owner_smoke import route_disk
        records=[]
        for n in (15,30,45,60):
            disk=BASE/f'route-{n}.atr';route=route_disk(n,r.B/'candidate.atr',disk)
            ev=[(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0)),(4600,4600,dict(stick=r.STICK[route['last_move']])),(4650,4650,dict(fire=0))]
            frames=list(range(4650,5351))+[4500,4630]
            out,s,l=probe(r.B,f'boundary-{n}',ev,frames,5380,image=disk.read_bytes())
            assert s[4630]['phase']==2 and s[4630]['scene']==n-1
            assert s[5350]['phase']==(10 if n==60 else 1)
            assert s[5350]['scene']==(59 if n==60 else n)
            records.append(dict(level=n,route=route,final=s[5350],out=str(out)))
        dump(DOC/'boundaries.json',dict(status='PASS',runs=records))
if __name__=='__main__':main()
