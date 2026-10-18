#!/usr/bin/env python3
"""Release candidate device-only tests. Every emulator launch is headless.

Reuses the independent audit's stimulus definitions, with assertions for the
fixed behavior, and the existing packed-media/live-raster oracle.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from product1_gauntlet import setup
from product1_fix1_review import live,sections
from finish2_probe import STAGES
from atr import offset
import gauntlet
import verify

BASE=Path('build/release1');B=BASE/'final';RESULTS=[]
L=json.loads(Path('assets/levels/camp2-b/campaign.json').read_text())['levels']
STICK={'U':14,'D':13,'L':11,'R':7};AT=offset(8100,128);PAL=35568

def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def probe(name,events,frames,total,build=None,image=None,stock=False,raster=True):
    b=build or B;labs=setup(b);native=gauntlet.run
    if os.environ.get('NEON_RELEASE1_OBSERVER'):
        os.environ['NEON_A5B_OBSERVER']=os.environ['NEON_RELEASE1_OBSERVER']
    if image is not None:
        media=BASE/'media';media.mkdir(exist_ok=True);p=media/(name+'.atr');p.write_bytes(image)
        def mounted(*a,**kw):kw['atr']=str(p);return native(*a,**kw)
        gauntlet.run=mounted
    try:out=gauntlet.probe(name,events,sorted(set(frames)),total,boot=True,patch=not stock,trace_override=STAGES)
    finally:gauntlet.run=native
    states={f:verify.state(out/f'frame-{f:04}.ram',labs) for f in frames};pixels=0
    for f,s in states.items():
        r=(out/f'frame-{f:04}.ram').read_bytes()
        for n in ('_save_error','_save_valid','_save_complete','_eng4_busy','_hud_dirty','_asset_loading'):
            s[n]=r[labs[n]]
        assert s['overflow']==s['publication_overflow']==0,(name,f,s)
        if raster and s['phase'] in (1,2):pixels+=live(out,f,labs,sections((out/'candidate.atr').read_bytes(),s['scene']))['pixels']
    RESULTS.append(dict(name=name,build=str(b),states=states,pixels=pixels,stock=stock,ATR_sha256=hashlib.sha256((b/'candidate.atr').read_bytes()).hexdigest(),status='PASS'))
    dump(BASE/'runtime-progress.json',RESULTS)
    return out,states,labs

def campaign(build=None,name='campaign-full'):
    b=build or B;oracle=json.loads((b/'independent-core/result.json').read_text())['levels']
    events=[(700,700,dict(fire=0))];frames=[650];f=1000;expected={};records=[]
    for i,l in enumerate(L):
        frames.append(f-5);expected[f-5]=(i,1,0,None)
        for c in l['path']:events.append((f,f,dict(stick=STICK[c])));f+=8
        frames.append(f+15);expected[f+15]=(i,2,len(l['path']),oracle[i])
        records.append(dict(level=i+1,frame=f+15,moves=len(l['path']),path=l['path']))
        events.append((f+30,f+30,dict(fire=0)));f+=330
    frames+=[f-5];out,ss,labs=probe(name,events,frames,f+10,build=b)
    for frame,(i,phase,moves,o) in expected.items():
        s=ss[frame];assert s['scene']==i and s['phase']==phase and s['moves']==moves,(frame,s)
        assert s['error']==s['late']==0
        if o:assert s['player']==o['final_player'] and sorted(s['boxes'])==sorted(o['final_boxes']) and s['pushes']==o['pushes']
    assert ss[f-5]['phase']==10 and ss[f-5]['scene']==59
    dump(out/'campaign-result.json',dict(status='PASS',levels=records,frames=f+10,final=ss[f-5],pixel_comparisons=RESULTS[-1]['pixels']))
    return out

def same(a,b):
    assert all(a[k]==b[k] for k in ('scene','player','boxes','moves','pushes')),(a,b)

def crc(b):
    c=65535
    for v in b:
        c^=v<<8
        for _ in range(8):c=((c<<1)^0x1021 if c&32768 else c<<1)&65535
    return c

def fix(r):r[126:]=crc(r[:126]).to_bytes(2,'little');return r
def with_slots(b,slots):
    d=bytearray((b/'candidate.atr').read_bytes());d[AT:AT+256]=b''.join(slots);return d

def saves():
    out,s,l=probe('two-generations',[(700,700,dict(fire=0)),(1000,1000,dict(stick=7)),(1050,1050,dict(consol=6)),(1080,1080,dict(consol=5)),(1350,1350,dict(stick=13)),(1380,1380,dict(fire=0)),(1700,1700,dict(stick=7)),(1750,1750,dict(consol=6)),(1780,1780,dict(consol=5))],[1030,1730,2100],2120)
    saved=(out/'candidate.atr').read_bytes();records=[saved[AT+i*128:AT+(i+1)*128] for i in range(2)]
    assert s[1030]['moves']==1 and s[1730]['moves']==2 and s[2100]['phase']==0
    assert all(r[:4]==b'NSAV' and crc(r[:126])==int.from_bytes(r[126:],'little') for r in records)
    resume=[(700,700,dict(stick=13)),(730,730,dict(fire=0))]
    _,cold,_=probe('cold-newest',resume,[1250],1280,image=saved);same(cold[1250],s[1730]);assert cold[1250]['undo']==0
    for slot in (0,1):
        os.environ.update(UX1_FAIL_SECTOR=str(8100+slot),UX1_FAIL_READS='100')
        try:o,t,_=probe(f'unreadable-slot-{slot}',[(700,700,dict(fire=0)),(1000,1000,dict(stick=7)),(1050,1050,dict(consol=6)),(1080,1080,dict(consol=5))],[1400],1420,image=saved)
        finally:os.environ.pop('UX1_FAIL_SECTOR');os.environ.pop('UX1_FAIL_READS')
        assert t[1400]['phase']==3 and t[1400]['_save_error']==4
        assert (o/'candidate.atr').read_bytes()[AT:AT+256]==saved[AT:AT+256]
    protected=bytearray(saved);protected[15]=1
    o,t,_=probe('write-protect',resume+[(1300,1300,dict(consol=6)),(1330,1330,dict(consol=5))],[1250,1500],1520,image=protected)
    assert t[1500]['phase']==3 and t[1500]['_save_error']==4
    assert (o/'candidate.atr').read_bytes()[AT:AT+256]==saved[AT:AT+256]
    for n in (1,16,31,46):
        b=BASE/f'test-{n}';path=L[n-1]['path'][:3]
        o,t,_=probe('stock-area',[],[2800],2820,build=b,stock=True)
        assert t[2800]['phase']==1 and t[2800]['scene']==n-1 and t[2800]['moves']==0
        ev=[(1000+i*8,1000+i*8,dict(stick=STICK[c])) for i,c in enumerate(path)]
        ev += [(1040+i*8,1040+i*8,dict(consol=5)) for i in range(len(path))]
        ev += [(1100,1100,dict(consol=3))]
        ev += [(1400+i*8,1400+i*8,dict(stick=STICK[c])) for i,c in enumerate(path)]
        ev += [(1500,1500,dict(consol=6)),(1530,1530,dict(consol=5))]
        o,t,_=probe('move-undo-restart-save',ev,[950,1030,1075,1350,1450,1800],1820,build=b)
        assert t[1030]['moves']==t[1450]['moves']==len(path)
        for f in (1075,1350):same(t[f],t[950]);assert t[f]['undo']==0
        assert t[1800]['phase']==0
        disk=(o/'candidate.atr').read_bytes()
        _,cold,_=probe('cold-save',[],[1000],1020,build=b,image=disk);same(cold[1000],t[1450]);assert cold[1000]['undo']==0
        # Semantic rejection of the newest record must attempt the older one.
        original=next(disk[AT+i*128:AT+(i+1)*128] for i in range(2) if disk[AT+i*128:AT+i*128+4]==b'NSAV')
        for kind in ('terrain','box-count','board-crc'):
            for order in (0,1):
                old=bytearray(original);old[8:10]=(65535).to_bytes(2,'little');fix(old)
                bad=bytearray(old);bad[8:10]=bytes(2)
                if kind=='terrain':bad[16:18]=bytes(2)
                elif kind=='box-count':bad[18]=2 if bad[18]==1 else bad[18]-1
                else:bad[14]^=1
                fix(bad);slots=[old,bad] if order==0 else [bad,old]
                _,t,_=probe(f'fallback-{kind}-{order}',[],[1400],1420,build=b,image=with_slots(b,slots))
                same(t[1400],cold[1000]);assert t[1400]['_save_error']==0
        bad=bytearray(original);bad[16:18]=bytes(2);fix(bad)
        _,t,_=probe('both-semantic-bad',[(1500,1500,dict(fire=0))],[1400,1600],1620,build=b,image=with_slots(b,[bad,bad]))
        assert all(x['phase']==8 and x['_save_error']==2 for x in t.values() if x is t[1400])
        assert t[1600]['phase']==0
        # Normal <-> test, and test -> a different test, never restore foreign state.
        foreign=with_slots(B,[original,original])
        _,t,_=probe(f'reject-test-{n}',resume,[1250],1280,image=foreign);assert t[1250]['phase']==8
        _,t,_=probe('reject-normal',[],[1000],1020,build=b,image=with_slots(b,records));assert t[1000]['phase']==8
        other=BASE/f'test-{16 if n==1 else 1}'
        _,t,_=probe(f'reject-other-{n}',[],[1000],1020,build=other,image=with_slots(other,[original,original]));assert t[1000]['phase']==8
    o,t,_=probe('stock-write',[(3200,3200,dict(fire=0)),(4600,4600,dict(stick=7)),(4700,4700,dict(consol=6)),(4750,4750,dict(consol=5))],[4650,5600],5620,stock=True)
    _,cold,_=probe('stock-cold',[(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0))],[4800],4820,stock=True,image=(o/'candidate.atr').read_bytes());same(t[4650],cold[4800]);assert cold[4800]['undo']==0

def errors():
    d=bytearray((B/'candidate.atr').read_bytes());d[offset(1101,128)]=0
    _,s,_=probe('bad-package',[(700,700,dict(fire=0)),(1100,1100,dict(fire=0)),(1400,1400,dict(consol=6))],[1000,1300,1600],1620,image=d)
    assert s[1000]['phase']==s[1300]['phase']==6 and s[1600]['phase']==0

def main():
    global B
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('campaign','saves','errors'));p.add_argument('--build',default=str(B));a=p.parse_args();B=Path(a.build)
    globals()[a.mode]()
    dump(B/(a.mode+'-tests.json'),dict(status='PASS',tests=RESULTS))

if __name__=='__main__':main()
