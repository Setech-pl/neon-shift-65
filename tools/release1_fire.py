#!/usr/bin/env python3
"""Sweep A-01 external pin phases and prove distinct full action rasters."""
import argparse
import csv
import json
import os
from pathlib import Path
import release1_runtime as r
from product1_gauntlet import setup
from product1_eng4 import analyze

def run(b,name,stick,shift=0,fire=4400,proof=False,image=None,initial='R',index=0,fresh=False):
    base=1139*r.PAL;wave=[[base+1800+shift,stick,1,7],[base+fire,stick,0,7],[base+r.PAL,15,1,7]]
    if fresh:wave.extend([[base+20*r.PAL,stick,1,7],[base+21*r.PAL,15,1,7],[base+30*r.PAL,15,0,7],[base+31*r.PAL,15,1,7]])
    pin=b/(name+'-pins.csv');pin.write_text(''.join(','.join(map(str,v))+'\n' for v in wave))
    os.environ.update(NSQ_PIN_SCHEDULE=str(pin.resolve()),ENG2_BUS_RANGE='1138,1156',NSQ_ACTION_AUDIT='1138,1156')
    l=setup(b);names=['_game_step','_undo_pop','_input_read','_eng4_accepted','_publish_now','publish_update','_foreground_publication_end','_gs','_count','_head','_input_head','_publish_pending','_poll_ready','_input_tail','_poll_stick','_poll_trigger','_poll_console']
    os.environ['NSQ_ACTION_ADDRS']=','.join(f'{l.get(n,0):04x}' for n in names)
    if proof:os.environ['NSQ_FETCH_RANGE']='1138,1155'
    events=[(700,700,dict(fire=0)),(1000,1000,dict(stick=r.STICK[initial[0]]))] if index==0 else [(700,700,dict(stick=13)),(730,730,dict(fire=0))]
    try:o,s,l=r.probe(name,events,list(range(1138,1156))+[1450],1470,build=b,image=image,raster=False)
    finally:
        for n in ('NSQ_PIN_SCHEDULE','ENG2_BUS_RANGE','NSQ_ACTION_AUDIT','NSQ_ACTION_ADDRS','NSQ_FETCH_RANGE'):os.environ.pop(n,None)
    rows=list(csv.DictReader((o/'action-state.csv').open()))
    steps=[q for q in rows if q['event']=='0' and q['edge']=='1']
    undos=[q for q in rows if q['event']=='1' and q['edge']=='1']
    accepted=[q for q in steps if q['a']=='1'];undone=[q for q in undos if q['a']=='1']
    assert s[1450]['_eng4_busy']==0,(name,s[1450])
    if proof:
        assert accepted and undone,(name,rows)
        analyze(b,o,'candidate',wave,1140,1155,'assets/levels/camp2-b/campaign.json',initial_path=initial,level_index=index,cold_prefix=index!=0)
        result=json.loads((o/'eng4-result.json').read_text());a=result['accepted_actions']
        assert [q['action'] for q in a]==['UDLR'[list(r.STICK.values()).index(stick)],'Z']
        assert a[0]['visible_frame']<a[1]['visible_frame']
    return dict(name=name,shift=shift,fire=fire,accepted=len(accepted),undos=len(undone),final=s[1450],out=str(o))

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);a=p.parse_args();b=Path(a.build);results=[]
    results.append(run(b,'audit-witness-proof',7,proof=True))
    assert results[-1]['final']['scene']==0 and results[-1]['final']['moves']==1
    for shift in range(-600,601,75):
        q=run(b,'sweep-win-'+str(shift+600),7,shift=shift);results.append(q)
        assert q['final']['scene']==0 and q['final']['moves'] in (0,1),q
    results.append(run(b,'nonwinning-proof',7,proof=True,initial='U'))
    # Initial Energy01: U is blocked after the first U. FIRE must still work,
    # and a rejected attempt must release busy without a publication timeout.
    for shift in (-600,-300,0,300,600):
        q=run(b,'sweep-block-'+str(shift+600),14,shift=shift,initial='U');results.append(q)
        assert q['accepted']==0 and q['final']['moves']==0 and q['final']['scene']==0,q
    q=run(b,'fresh-fire-after-ready',7,fresh=True);results.append(q)
    assert q['final']['scene']==1 and q['final']['phase']==1,q
    r.dump(b/'fire-tests.json',dict(status='PASS',tests=results,method='Original audit pin witness, 17 direction phases around first DLI, five blocked phases, full fetch-raster proof, fresh FIRE after ready'))

if __name__=='__main__':main()
