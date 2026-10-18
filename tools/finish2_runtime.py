#!/usr/bin/env python3
"""Changed RC2 paths: full disk boot, raster stability, saves and error UI."""
import json
from pathlib import Path
from product1_gauntlet import setup
from product1_fix1_review import live,sections
from atr import offset
from finish2_probe import STAGES
import gauntlet
import verify

BASE=Path('build/finish2')
NORMAL=BASE/'final'
OLD=Path('build/finish1/rc1')
LEVELS=json.loads(Path('assets/levels/camp2-b/campaign.json').read_text())['levels']
STICK={'U':14,'D':13,'L':11,'R':7}
RESULTS=[]

def probe(b,name,events,frames,total,stock=False,image=None):
    labs=setup(b);native=gauntlet.run
    if image is not None:
        p=BASE/'media';p.mkdir(exist_ok=True);disk=p/(name+'.atr');disk.write_bytes(image)
        def run(*args,**kw):kw['atr']=str(disk);return native(*args,**kw)
        gauntlet.run=run
    try:out=gauntlet.probe(name,events,frames,total,boot=True,patch=not stock,trace_override=STAGES)
    finally:gauntlet.run=native
    states={f:verify.state(out/f'frame-{f:04}.ram',labs) for f in frames}
    pixels=0
    for f,s in states.items():
        assert s['overflow']==s['publication_overflow']==0,(name,f,s)
        if s['phase'] in (1,2):
            assert s['error']==0
            pixels+=live(out,f,labs,sections((out/'candidate.atr').read_bytes(),s['scene']))['pixels']
    RESULTS.append(dict(name=name,build=str(b),out=str(out),stock=stock,states=states,pixels=pixels,status='PASS'))
    return out,states,labs

def same(a,b):
    assert all(a[k]==b[k] for k in ('scene','player','boxes','moves','pushes')),(a,b)

def mount(b,save):
    data=bytearray((b/'candidate.atr').read_bytes());at=offset(8100,128)
    data[at:at+256]=save.read_bytes()[at:at+256];return data

def hardware_areas():
    saves=[]
    for number in (1,16,31,46):
        b=BASE/f'test-{number}';path=LEVELS[number-1]['path'][:3]
        # Every delivered test image also cold-boots with actual OS serial I/O.
        out,s,l=probe(b,'stock-area',[],[2700,2701,2702,2800],2820,stock=True)
        for state in s.values():assert state['scene']==number-1 and state['phase']==1 and state['moves']==state['undo']==0
        events=[(1000+i*8,1000+i*8,dict(stick=STICK[c])) for i,c in enumerate(path)]
        events += [(1040+i*8,1040+i*8,dict(consol=5)) for i in range(len(path))]
        events += [(1100,1100,dict(consol=3))]
        events += [(1400+i*8,1400+i*8,dict(stick=STICK[c])) for i,c in enumerate(path)]
        events += [(1500,1500,dict(consol=6)),(1530,1530,dict(consol=5))]
        out,s,l=probe(b,'move-undo-restart-save',events,[950,1030,1075,1350,1450,1520,1800],1820)
        assert s[1030]['moves']==s[1450]['moves']==len(path)
        for f in (1075,1350):same(s[f],s[950]);assert s[f]['undo']==0
        assert s[1520]['phase']==3 and s[1800]['phase']==0
        saved=out/'candidate.atr';saves.append(saved)
        _,cold,_=probe(b,'cold-test-save',[],[950],980,image=saved.read_bytes())
        same(cold[950],s[1450]);assert cold[950]['undo']==0
        _,rejected,_=probe(NORMAL,f'reject-test-{number:02}',[(700,700,dict(stick=13)),(720,720,dict(fire=0))],[1200],1220,image=mount(NORMAL,saved))
        assert rejected[1200]['phase']==8
    # A different test area must not inherit another area's saved board.
    b=BASE/'test-16'
    _,s,l=probe(b,'reject-other-test',[],[950],980,image=mount(b,saves[0]))
    assert s[950]['scene']==15 and s[950]['moves']==s[950]['undo']==0
    # Normal campaign save is rejected by the test namespace as well.
    prior=OLD/'rc1-stock-sio-save/candidate.atr'
    _,s,_=probe(b,'reject-normal-save',[],[950],980,image=mount(b,prior))
    assert s[950]['scene']==15 and s[950]['moves']==s[950]['undo']==0

def normal_saves():
    # Stock writes, readback and cold Continue on the normal RC2.
    out,s,_=probe(NORMAL,'stock-save',[(3200,3200,dict(fire=0)),(4600,4600,dict(stick=7)),
                    (4700,4700,dict(consol=6)),(4750,4750,dict(consol=5))],[4650,5600],5620,stock=True)
    assert s[4650]['moves']==s[4650]['pushes']==1 and s[5600]['phase']==0
    saved=out/'candidate.atr'
    _,cold,_=probe(NORMAL,'stock-cold',[(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0))],[4800],4820,stock=True,image=saved.read_bytes())
    same(cold[4800],s[4650]);assert cold[4800]['undo']==0
    # Bidirectional save-format compatibility with RC1 (same campaign/CRC).
    resume=[(700,700,dict(stick=13)),(720,720,dict(fire=0))]
    _,back,_=probe(OLD,'finish2-rc2-to-rc1',resume,[1200],1220,image=mount(OLD,saved))
    same(back[1200],s[4650])
    out,forward,_=probe(NORMAL,'rc1-to-rc2',resume+[(1250,1250,dict(consol=5)),(1280,1280,dict(consol=3))],
                       [1200,1260,1595],1620,image=mount(NORMAL,OLD/'rc1-stock-sio-save/candidate.atr'))
    same(forward[1200],forward[1260]);assert forward[1200]['moves']==1
    assert forward[1595]['moves']==forward[1595]['undo']==0

def energy02():
    path=LEVELS[0]['path'];events=[(700,700,dict(fire=0))]
    events += [(1000+i*8,1000+i*8,dict(stick=STICK[c])) for i,c in enumerate(path)]
    end=1000+len(path)*8;events.append((end+20,end+20,dict(fire=0)))
    frames=list(range(end+230,end+251))+[end+300,end+350]
    out,s,l=probe(NORMAL,'energy02-stability',events,frames,end+370)
    for state in s.values():
        assert state['scene']==1 and state['phase']==1 and state['moves']==state['undo']==0
    # Same complete board and object ownership over consecutive full rasters;
    # background animations may evolve, and are checked by the live oracle.
    assert all(state['player']==s[frames[0]]['player'] and state['boxes']==s[frames[0]]['boxes'] for state in s.values())

def error_paths():
    image=bytearray((NORMAL/'candidate.atr').read_bytes());image[offset(1101,128)]=0
    _,s,_=probe(NORMAL,'invalid-asset',[(700,700,dict(fire=0)),(1100,1100,dict(fire=0)),
                          (1400,1400,dict(consol=6))],[1000,1300,1600],1620,image=image)
    assert s[1000]['phase']==s[1300]['phase']==6 and s[1600]['phase']==0

def main():
    hardware_areas();normal_saves();energy02();error_paths()
    Path('docs/finish2/runtime.json').write_text(json.dumps(dict(status='PASS',tests=RESULTS,
          hardware='NOT_RUN',method='Cold ATR boot, emulated PORTA/TRIG0/CONSOL only; no writes to target RAM'),indent=2)+'\n')
    print('PASS RC2 changed paths:',len(RESULTS),'probes',sum(r['pixels'] for r in RESULTS),'pixels',flush=True)

if __name__=='__main__':main()
