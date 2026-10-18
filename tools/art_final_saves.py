#!/usr/bin/env python3
"""Campaign isolation and art-update save compatibility using actual game saves."""
import hashlib
import json
import struct
from pathlib import Path
from product1_gauntlet import setup
from atr import offset
from warehouses import crc16
from product1_fix1_review import live,sections
import gauntlet
import verify

BASE=Path('build/art-final')


def main():
    builds={'final':BASE/'final','same-campaign-before':Path('build/recovery1/owner-vis1r2'),
            'old-camp2b':Path('build/camp2-b-20261015/runtime')}
    media=BASE/'save-media';media.mkdir(exist_ok=False);results=[]
    def with_save(build,source):
        image=bytearray((build/'candidate.atr').read_bytes());at=offset(8100,128)
        image[at:at+256]=source.read_bytes()[at:at+256]
        return image
    def probe(name,variant,image,events,frames,total,expected_phase,expected_state=None,patch=True):
        build=builds[variant];labs=setup(build);gauntlet.ROOT=BASE/'final'
        fixture=media/(name+'.atr');fixture.write_bytes(image);native=gauntlet.run
        def run(*args,**kw):kw['atr']=str(fixture);return native(*args,**kw)
        gauntlet.run=run
        try:
            # Labels/program remain the target's own, even for reverse tests.
            for ext in ('lbl','xex'): (BASE/'final'/('save-test.'+ext)).write_bytes((build/('candidate.'+ext)).read_bytes())
            out=gauntlet.probe(name,events,frames,total,boot=True,variant='save-test',patch=patch)
        finally:gauntlet.run=native
        states={f:verify.state(out/f'frame-{f:04}.ram',labs) for f in frames}
        last=states[frames[-1]]
        assert last['phase']==expected_phase and all(s['error']==s['overflow']==s['publication_overflow']==0 for s in states.values())
        error=(out/f'frame-{frames[-1]:04}.ram').read_bytes()[labs['_save_error']]
        if expected_phase==8:assert error==2
        if expected_state:
            assert all(last[k]==expected_state[k] for k in ('scene','player','boxes','moves','pushes'))
            assert last['undo']==0
            live(out,frames[-1],labs,sections(image,last['scene']))
        results.append(dict(name=name,target=variant,status='PASS',states=states,save_error=error,
                            input_ATR_sha256=hashlib.sha256(image).hexdigest(),out=str(out),stock_OS_SIO=not patch))
        print('PASS save',name,flush=True)
        return out,states
    resume=[(700,700,dict(stick=13)),(720,720,dict(fire=0))]
    oldsave=Path('build/camp2-b-20261015/runtime/sample-08-cold/candidate.atr')
    final_records=json.loads((BASE/'captures-final.json').read_text());before_records=json.loads((BASE/'captures-before.json').read_text())
    new_save=Path(final_records[2]['out'])/'candidate.atr'
    probe('reject-original-camp2b','final',with_save(builds['final'],oldsave),resume,[1200],1250,8)
    probe('old-camp2b-rejects-new','old-camp2b',with_save(builds['old-camp2b'],new_save),resume,[1200],1250,8)
    for index in (0,1,2):
        before,final=before_records[index],final_records[index]
        probe(f"same-campaign-before-to-final-{final['number']:02d}",'final',
              with_save(builds['final'],Path(before['out'])/'candidate.atr'),resume,[1200],1250,1,before['states'][str(before['partial'])])
    probe('same-campaign-final-to-before','same-campaign-before',with_save(builds['same-campaign-before'],new_save),resume,[1200],1250,1,
          final_records[2]['states'][str(final_records[2]['partial'])])
    damaged=with_save(builds['final'],new_save)
    for sector in (8100,8101):
        at=offset(sector,128)
        if damaged[at:at+4]==b'NSAV':
            damaged[at+14]^=1;struct.pack_into('<H',damaged,at+126,crc16(damaged[at:at+126]))
    probe('reject-matching-id-wrong-board-crc','final',damaged,resume,[1200],1250,8)
    # New campaign + final art through real OS SIO, no SIO patch.
    original=(builds['final']/'candidate.atr').read_bytes()
    out,states=probe('stock-sio-new-save','final',original,
                     [(3200,3200,dict(fire=0)),(4600,4600,dict(stick=7)),(4700,4700,dict(consol=6)),(4750,4750,dict(consol=5))],
                     [4500,4650,5600],5650,0,patch=False)
    assert states[4650]['scene']==0 and states[4650]['moves']==states[4650]['pushes']==1
    probe('stock-sio-new-cold','final',(out/'candidate.atr').read_bytes(),
          [(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0))],[4800],4850,1,states[4650],patch=False)
    (BASE/'save-results.json').write_text(json.dumps(dict(status='PASS',tests=results,
                 identity='Same raw campaign SHA/board CRC remains compatible across art updates; old campaign rejected both directions',
                 save_format='NSAV v1 unchanged; no migration or silent map reset'),indent=2)+'\n')


if __name__=='__main__':main()
