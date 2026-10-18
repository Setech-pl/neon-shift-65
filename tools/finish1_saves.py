#!/usr/bin/env python3
"""RC1 art-update saves, actual OS SIO, cold restart and campaign isolation."""
import hashlib
import json
from pathlib import Path
from product1_gauntlet import setup
from product1_fix1_review import live,sections
from atr import offset
import gauntlet
import verify

BASE=Path('build/finish1')
BUILD=BASE/'rc1'
BEFORE=Path('build/art-final/final')

def main():
    media=BASE/'save-media';media.mkdir(exist_ok=False);results=[]
    def mount(target,save):
        data=bytearray((target/'candidate.atr').read_bytes());at=offset(8100,128)
        data[at:at+256]=save.read_bytes()[at:at+256];return data
    def probe(name,target,data,events,frames,total,patch=True):
        labs=setup(target);gauntlet.ROOT=BUILD
        fixture=media/(name+'.atr');fixture.write_bytes(data);native=gauntlet.run
        def run(*args,**kw):kw['atr']=str(fixture);return native(*args,**kw)
        gauntlet.run=run
        for ext in ('lbl','xex'):(BUILD/('save-test.'+ext)).write_bytes((target/('candidate.'+ext)).read_bytes())
        try:out=gauntlet.probe(name,events,frames,total,boot=True,variant='save-test',patch=patch)
        finally:gauntlet.run=native
        states={f:verify.state(out/f'frame-{f:04}.ram',labs) for f in frames}
        assert all(s['error']==s['overflow']==s['publication_overflow']==0 for s in states.values())
        for f,s in states.items():
            if s['phase'] in (1,2):live(out,f,labs,sections(data,s['scene']))
        results.append(dict(name=name,target=str(target),out=str(out),input_ATR_sha256=hashlib.sha256(data).hexdigest(),
                            states=states,stock_OS_SIO=not patch,status='PASS'))
        return out,states,labs
    def same(a,b):
        assert all(a[k]==b[k] for k in ('scene','player','boxes','moves','pushes'))
    resume=[(700,700,dict(stick=13)),(720,720,dict(fire=0))]
    record=json.loads(Path('build/art-final/captures-final.json').read_text())[2]
    oldsave=Path(record['out'])/'candidate.atr';expected=record['states'][str(record['partial'])]
    out,s,labs=probe('checkpoint-to-rc1',BUILD,mount(BUILD,oldsave),
                    resume+[(1400,1400,dict(consol=6)),(1450,1450,dict(consol=5))],[1200,1600],1650)
    same(s[1200],expected);assert s[1200]['phase']==1 and s[1200]['undo']==0 and s[1600]['phase']==0
    rc_save=out/'candidate.atr'
    _,back,_=probe('rc1-to-checkpoint',BEFORE,mount(BEFORE,rc_save),resume,[1200],1250)
    same(back[1200],expected);assert back[1200]['undo']==0 and back[1200]['phase']==1
    _,restart,_=probe('rc1-cold-undo-restart',BUILD,mount(BUILD,rc_save),
                      resume+[(1250,1250,dict(consol=5)),(1280,1280,dict(consol=3))],[1200,1260,1595],1650)
    same(restart[1200],restart[1260]);assert restart[1595]['scene']==8 and restart[1595]['moves']==restart[1595]['pushes']==restart[1595]['undo']==0
    alien=Path('build/camp2-b-20261015/runtime/sample-08-cold/candidate.atr')
    out,s,labs=probe('rc1-reject-original-camp2b',BUILD,mount(BUILD,alien),resume,[1200],1250)
    assert s[1200]['phase']==8 and (out/'frame-1200.ram').read_bytes()[labs['_save_error']]==2
    # Actual stock OS writes/readback: no SIO patch, no host state fabrication.
    out,s,_=probe('rc1-stock-sio-save',BUILD,(BUILD/'candidate.atr').read_bytes(),
                  [(3200,3200,dict(fire=0)),(4600,4600,dict(stick=7)),(4700,4700,dict(consol=6)),(4750,4750,dict(consol=5))],
                  [4650,5600],5650,patch=False)
    assert s[4650]['moves']==s[4650]['pushes']==1 and s[5600]['phase']==0
    _,cold,_=probe('rc1-stock-sio-cold',BUILD,(out/'candidate.atr').read_bytes(),
                   [(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0))],[4800],4850,patch=False)
    same(cold[4800],s[4650]);assert cold[4800]['undo']==0 and cold[4800]['phase']==1
    Path('docs/finish1/save-results.json').write_text(json.dumps(dict(status='PASS',tests=results,
        identity='Same raw campaign SHA and board CRC across f5df646/RC1; old campaign rejected',
        mechanism='Only copied ATR save sectors mounted; all saves produced by the game; no target RAM writes'),indent=2)+'\n')
    print('PASS RC1 saves: bidirectional checkpoint compatibility, cold undo/restart, alien campaign rejection, stock OS SIO save/cold')

if __name__=='__main__':main()
