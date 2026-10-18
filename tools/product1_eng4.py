#!/usr/bin/env python3
"""External pins -> actual observations -> admitted requests -> full rasters."""
import argparse,csv,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'experiments/eng3-observed-input-3pal'),str(ROOT/'experiments/renderer-a5c'),str(ROOT/'tools'),str(ROOT/'experiments/art3-contextual-decoration-review')]
import gauntlet,verify,pixel_fast,fetch_oracle,turbo_run
from observed_oracle import PAL,transactions,runtime_read_pcs,Game,board_matches
from floor_restore import packages
from atr import offset

def rows(p):return list(csv.DictReader(p.open()))
def state(s):
    b=bytes.fromhex(s)
    return dict(player=list(b[762:764]),boxes=[list(b[764+i*2:766+i*2]) for i in range(b[784])],moves=int.from_bytes(b[785:789],'little'),pushes=int.from_bytes(b[789:793],'little'))

def analyze(B,out,variant,wave,start,end,campaign='assets/levels/product1-campaign.json',initial_path='',level_index=0,cold_prefix=False):
    product=(B/'campaign-id.h').exists()
    labs=verify.labels(B/(variant+'.lbl'));level=json.loads((ROOT/campaign).read_text())['levels'][level_index]['rows'] if product else json.loads((B/'levels.json').read_text())['levels'][1 if variant=='carry' else 0]['rows']
    seed=3999999999 if variant=='carry' else 0;game=Game(level,seed)
    for c in initial_path:game.request(c)
    if cold_prefix:game.history=[]
    pcs=runtime_read_pcs(B/(variant+'.xex'))
    bus=[r for r in rows(out/'device-reads.csv') if int(r['pc']) in pcs]
    # The finite trace window may open during a regular three-query probe.
    # Drop only that leading partial transaction; retain strict grouping of
    # every subsequent query and all original external stimulus timestamps.
    leading=[]
    while bus and int(bus[0]['address'])!=0xd300:leading.append(bus.pop(0))
    assert len(leading)<=2
    obs,capture=transactions(bus,pcs);capture['leading_partial_queries']=leading
    # Trace chronology is independent of the candidate's intention flags.
    timeline=[(o['completed'],0,o) for o in obs]
    timeline += [(int(r['clock']),1,r) for r in rows(out/'action-state.csv')]
    timeline.sort(key=lambda r:(r[0],r[1]))
    buttons=0;pending={};latest=None;request=None;entry={};actions=[];requests=[]
    def external(clock,index,active):
        old=[15,1,7];origin=None
        for e in wave:
            if e[0]>=clock:break
            if e[index+1]!=old[index] and active(e[index+1]):origin=e[0]
            old=e[1:]
        return origin
    for clock,kind,r in timeline:
        if kind==0:
            stick,trig,con=r['values'];b=(not trig)|((not(con&2))<<1)|((not(con&4))<<2)|((not(con&1))<<3)
            edges=b&~buttons;buttons=b;latest=r
            for bit in (1,2,4,8):
                if edges&bit and bit not in pending:
                    idx=1 if bit==1 else 2
                    t0=external(clock,idx,(lambda v:v==0) if bit==1 else (lambda v,mask={2:2,4:4,8:1}[bit]:not(v&mask)))
                    pending[bit]=(t0,r['completed'])
        else:
            event=int(r['event']);edge=int(r['edge']);a=int(r['a'])
            if event==2 and edge==1 and a:
                code={1:'U',2:'D',3:'L',4:'R',5:'Z',6:'S',7:'Z',8:'OPTION'}[a]
                if a<=4:assert not any(bit in pending for bit in (1,2)),('direction before pending undo',r)
                if a in (5,7):
                    origins=[pending.pop(bit) for bit in (1,2) if bit in pending]
                    assert origins,('undo without observed edge',clock)
                    t0,oc=min(origins)
                elif a in (6,8):t0,oc=pending.pop(8 if a==6 else 4)
                else:
                    t0=external(clock,0,lambda v:v!=15);oc=latest['completed']
                request=dict(action=code,request_clock=clock,t0=t0,observation_completed=oc)
                requests.append(request)
            if event in (0,1) and edge==0:entry[event]=clock
            if event in (0,1) and edge==1:
                assert request
                c='Z' if event==1 else request['action'];expected=game.request(c)
                actual=state(r['gs_hex'])
                assert expected['state']==actual,(clock,c,expected,actual)
                assert expected['accepted']==a and expected['undo']==int(r['count'])
                if a:actions.append(dict(**request,accepted_clock=entry[event],return_clock=clock,state=actual,undo=int(r['count'])))
    captures=list(range(start-2,end+1))
    if product:
        raw=(B/(variant+'.atr')).read_bytes()[offset(1101+level_index*70,128):];sections={}
        for i in range(raw[6]):
            at=16+i*8;addr=int.from_bytes(raw[at:at+2],'little');size=int.from_bytes(raw[at+2:at+4],'little');pos=int.from_bytes(raw[at+4:at+6],'little');sections[addr]=raw[144+pos:144+pos+size]
    else:sections=packages((B/(variant+'.atr')).read_bytes())[1 if variant=='carry' else 0]
    # Derive the actual DMA raster, checking stable values and every pixel.
    verify.pixel_reference=pixel_fast.pixel
    old=verify.check
    def check(path,frames):return [verify.pixel(path,f,labs) for f in frames]
    verify.check=check
    try:fetch_oracle.check(out,captures)
    finally:verify.check=old
    clocks={int(r['frame']):int(r['clock']) for r in rows(out/'input-clock.csv')}
    previous=start-3
    for a in actions:
        found=None
        for f in captures:
            if f<=previous:continue
            rp=out/f'fetch-oracle/raster-{f:04}.ram'
            if not rp.exists():continue
            ram=rp.read_bytes()
            if not board_matches(ram,a['state'],level,sections):continue
            # Both logical counter values must have reached the live HUD.
            if any(int.from_bytes(ram[labs[n]:labs[n]+4],'little')!=a['state'][key] for n,key in [('hud_live_moves','moves'),('hud_live_pushes','pushes')]):continue
            found=f;break
        assert found is not None,('accepted state missing full image',a)
        previous=found
        bottom=24+(13-len(level)+2*(len(level)-1))*8+16+8
        visible=clocks[found]+bottom*114+8
        a.update(visible_frame=found,visible_upper_clock=visible,external_to_accept_pal=(a['accepted_clock']-a['t0'])/PAL,
                 observed_to_accept_pal=(a['accepted_clock']-a['observation_completed'])/PAL,
                 accept_to_full_pal=(visible-a['accepted_clock'])/PAL,external_to_full_pal=(visible-a['t0'])/PAL)
    result=dict(contract='ENG4',variant=variant,ATR_sha256=hashlib.sha256((B/(variant+'.atr')).read_bytes()).hexdigest(),physical_waveform=wave,observations=obs,capture=capture,requests=requests,accepted_actions=actions,
                exactly_one_ordered_full_image_per_accepted_action=True,logic_and_undo_oracle='PASS',status='MEASURED',maxima={k:max((a[k] for a in actions),default=0) for k in ['external_to_accept_pal','observed_to_accept_pal','accept_to_full_pal','external_to_full_pal']})
    (out/'eng4-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['maxima'],flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--name',default='qualification');p.add_argument('--length',type=int,default=9);p.add_argument('--variant',default='carry');p.add_argument('--wave');p.add_argument('--analyze',action='store_true');p.add_argument('--campaign',default='assets/levels/product1-campaign.json');a=p.parse_args()
    B=Path(a.build);out=B/a.name;start=1140;end=start+a.length+25
    wave=[[40511952+i*PAL+12,(7,14,7,13)[i%4],0 if i%2==0 else 1,7] for i in range(a.length)]
    wave.append([40511952+a.length*PAL+12,15,1,7])
    if a.wave:
        wave=json.loads(Path(a.wave).read_text());end=start+(wave[-1][0]-40511952)//PAL+30
    if not a.analyze:
        out.mkdir();(out/'pins.csv').write_text(''.join(','.join(map(str,r))+'\n' for r in wave))
        gauntlet.ROOT=B;labs=verify.labels(B/(a.variant+'.lbl'))
        os.environ.update(NSQ_PIN_SCHEDULE=str((out/'pins.csv').resolve()),NEON_A5B_OBSERVER=str((ROOT/'build/eng3-observed-input-3pal/observer/src/atari800').resolve()),NEON_ATARI_CONFIG=str((ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg').resolve()),NSQ_ACTION_AUDIT=f'{start-4},{end+1}',ENG2_BUS_RANGE=f'{start-4},{end+1}',NSQ_FETCH_RANGE=f'{start-2},{end+1}')
        names=['_game_step','_undo_pop','_input_read','_input_tick','_publish_now','publish_update','_foreground_publication_end','_gs','_count','_head','_input_head','_publish_pending','_poll_ready','_input_tail','_poll_stick','_poll_trigger','_poll_console']
        os.environ['NSQ_ACTION_ADDRS']=','.join(f'{labs.get(n,0):04x}' for n in names)
        gauntlet.probe(a.name,[(700,700,dict(fire=0))],list(range(start-2,end+1)),end+5,variant=a.variant,boot=True)
    analyze(B,out,a.variant,wave,start,end,a.campaign)
if __name__=='__main__':main()
