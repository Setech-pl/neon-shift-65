#!/usr/bin/env python3
"""Additional current-media fallback, invalid-save UI and undo256 witnesses."""
from pathlib import Path
import release1_runtime as r
from product1_eng4 import Game

def main():
    image=(r.B/'two-generations/candidate.atr').read_bytes()
    records=[image[r.AT+i*128:r.AT+(i+1)*128] for i in range(2)]
    for kind in ('terrain','board-crc','record-crc'):
        for order in (0,1):
            old=bytearray(records[0]);old[8:10]=(65535).to_bytes(2,'little');r.fix(old)
            bad=bytearray(records[1]);bad[8:10]=bytes(2)
            if kind=='terrain':bad[16:18]=bytes(2)
            if kind=='board-crc':bad[14]^=1
            r.fix(bad)
            if kind=='record-crc':bad[126]^=1
            slots=[old,bad] if order==0 else [bad,old]
            _,s,_=r.probe('normal-fallback-'+kind+'-'+str(order),[(700,700,dict(stick=13)),(730,730,dict(fire=0))],[1400],1420,image=r.with_slots(r.B,slots))
            assert s[1400]['phase']==1 and s[1400]['moves']==1
    r.dump(Path('docs/release1/normal-fallback.json'),dict(status='PASS',tests=r.RESULTS))
    r.RESULTS=[];b=r.BASE/'test-46';path=r.L[45]['path'][:270]
    events=[(1000+i*8,1000+i*8,dict(stick=r.STICK[c])) for i,c in enumerate(path)]
    events +=[(3200+i*8,3200+i*8,dict(consol=5)) for i in range(256)]
    _,s,_=r.probe('undo256-from-ATR',events,[950,3180,5260,5300],5320,build=b)
    g=Game(r.L[45]['rows'])
    for c in path[:14]:g.request(c)
    expected=g.state();assert s[3180]['undo']==256 and s[3180]['moves']==270
    for f in (5260,5300):
        for k in expected:assert s[f][k]==expected[k],(k,s[f],expected)
        assert s[f]['undo']==0
    r.dump(Path('docs/release1/undo256.json'),dict(status='PASS',tests=r.RESULTS,expected_prefix14=expected))

if __name__=='__main__':main()
