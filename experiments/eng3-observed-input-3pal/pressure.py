"""Achievable R+F/U/R+F/D producer, whole-PAL pins, no target RAM writes."""
from pathlib import Path
import os,sys,json,csv,hashlib
sys.path.insert(0,'experiments/renderer-a5c')
sys.path.insert(0,'tools')
import gauntlet,verify,fetch_oracle,pixel_fast,turbo_run
from emulator_smoke import run as native_run
from observed_oracle import transactions,runtime_read_pcs,expected,board_matches,PAL
sys.path.insert(0,'experiments/art3-contextual-decoration-review')
from floor_restore import packages
from m1_check import png

area=int(sys.argv[1]);length=int(sys.argv[2]) if len(sys.argv)>2 else 450
variant='candidate' if '--default' in sys.argv else 'carry'
seed=0 if variant=='candidate' else 3999999999
B=Path(f'build/eng3-observed-input-3pal/area-{area}');out=B/(f'pressure-{length}' + ('-default' if variant=='candidate' else ''))
analyze_only='--analyze-only' in sys.argv
if not analyze_only:assert not out.exists();out.mkdir()
gauntlet.ROOT=B;verify.pixel_reference=pixel_fast.pixel
start=1140;origin=40511952;l=verify.labels(B/(variant+'.lbl'))
wave=[]
for i in range(length):
    stick=(7,14,7,13)[i%4];fire=0 if i%2==0 else 1
    wave.append([origin+i*PAL+12,stick,fire,7])
wave.append([origin+length*PAL+12,15,1,7])
(out/'pins.csv').write_text(''.join(','.join(map(str,e))+'\n' for e in wave))
os.environ.update(NSQ_PIN_SCHEDULE=str((out/'pins.csv').resolve()),NEON_A5B_OBSERVER=str(Path('build/eng3-observed-input-3pal/observer/src/atari800').resolve()),ENG2_BUS_RANGE=f'{start},{start+length+30}',NSQ_ACTION_AUDIT=f'{start-1},{start+length+30}',NSQ_INPUT_AUDIT=f'{start},{start+6}',NSQ_FETCH_RANGE=f'{start-1},{start+length+30}')
names=['_game_step','_undo_pop','_input_read','_input_tick','_publish_now','publish_update','_foreground_publication_end','_gs','_count','_head','_input_head','_publish_pending','_poll_ready','_input_tail','_poll_stick','_poll_trigger','_poll_console']
os.environ['NSQ_ACTION_ADDRS']=','.join(f'{l.get(n,0):04x}' for n in names)
os.environ['NSQ_INPUT_AUDIT_ADDRS']=','.join(f'{l.get(n,0):04x}' for n in ['_poll_stick','_poll_trigger','_poll_console','_poll_last_stick','_poll_last_trigger','_poll_last_console','_input_head','_input_tail','_count','_head','_publish_pending','_poll_ready'])
def run(name,*a,**kw):kw['boot']=True;return native_run(str(out.relative_to('build')),*a,**kw)
gauntlet.run=run
captures=sorted(set(range(start-1,start+45))|set(range(start+length-8,start+length+31)))
prelude=[(700,700,dict(fire=0))]
if variant=='candidate':prelude += [(900,900,dict(consol=6)),(920,920,dict(stick=7)),(940,940,dict(consol=3))]
if not analyze_only:gauntlet.probe(out.name,prelude,captures,max(captures)+5,variant=variant,boot=True)
# Pixel measurement is independent of the overflow qualification gate. Preserve
# actual overflow values; the inherited aggregate checker stopped before pixels.
def measured_check(path,frames):
    pixels=[verify.pixel(path,f,l) for f in frames]
    states=[dict(frame=f,**verify.state(Path(path)/f'frame-{f:04}.ram',l)) for f in frames]
    r=dict(status='PIXEL_MEASUREMENT_PASS',states=states,pixels=pixels,engine='FAIL evaluated separately; overflow retained')
    (Path(path)/'pixel-measurement.json').write_text(json.dumps(r,indent=2)+'\n')
    return r
verify.check=measured_check
fetch_oracle.check(out,captures)
def rows(p):return [{k:(v if k=='gs_hex' else int(v)) for k,v in r.items()} for r in csv.DictReader(p.open())]
obs,capture=transactions(rows(out/'device-reads.csv'),runtime_read_pcs(B/(variant+'.xex')))
levelrows=json.loads((B/'levels.json').read_text())['levels'][1]['rows']
oracle=expected(obs,levelrows,wave,'',seed)
actual=[];selected=None
def state(hexbytes):
    b=bytes.fromhex(hexbytes)
    return dict(player=list(b[762:764]),boxes=[list(b[764+i*2:766+i*2]) for i in range(b[784])],moves=int.from_bytes(b[785:789],'little'),pushes=int.from_bytes(b[789:793],'little'))
for r in rows(out/'action-state.csv'):
    if r['event']==2 and r['edge']==1:selected=r['a']
    if r['event'] in (0,1) and r['edge']==1 and r['clock']>=wave[0][0]:
        actual.append(dict(action='Z' if r['event']==1 else {1:'U',2:'D',3:'L',4:'R'}[selected],clock=r['clock'],accepted=r['a'],undo=r['count'],state=state(r['gs_hex'])))
# The observed stream can exceed the final drained consumer range; retain prefix comparison explicitly.
legal_prefix=all(all(a[k]==e[k] for k in ['action','accepted','undo','state']) for a,e in zip(actual,oracle))
sections=packages((B/(variant+'.atr')).read_bytes())[1];clocks={r['frame']:r['clock'] for r in rows(out/'input-clock.csv')}
images=[];last=start-2;previous=[4,8];boxes=[[x,y] for y,row in enumerate(levelrows) for x,c in enumerate(row) if c in '$*']
for e in [x for x in oracle if x['accepted']][:22]:
    matches=[f for f in captures if f>last and f>=start and (out/f'fetch-oracle/raster-{f:04}.ram').exists() and board_matches((out/f'fetch-oracle/raster-{f:04}.ram').read_bytes(),e['state'],levelrows,sections)]
    if not matches:break
    f=matches[0];im,pal=png(out/f'native-{f:04}.png');old,op=png(out/f'native-{max(start-1,last):04}.png')
    bx,by=20-len(levelrows[0]),13-len(levelrows);px,py=e['state']['player'];x0=8+(bx+2*px)*8;y0=24+(by+2*py)*8
    changed=[y for y in range(y0,y0+16) for x in range(x0,x0+16) if pal[im[y][x]]!=op[old[y][x]]]
    affected=[previous,e['state']['player']]+[x for pair in zip(boxes,e['state']['boxes']) if pair[0]!=pair[1] for x in pair]
    upper=clocks[f]+(24+(by+2*max(x[1] for x in affected))*8+16+8)*114+8-e['t0']
    first=clocks[f]+(min(changed)+9)*114+8-e['t0'] if changed else None
    images.append(dict(action=e['action'],t0=e['t0'],visible_frame=f,first_interval_pal=[(first-130)/PAL,first/PAL] if first else None,full_interval_pal=[(upper-130)/PAL,upper/PAL],gate='PASS' if upper<=3*PAL and first is not None and first<=3*PAL else 'FAIL'))
    last=f;previous=e['state']['player'];boxes=e['state']['boxes']
schedule=rows(out/'frame-schedule.csv');peak=max((r['queue']&127) for r in schedule if r['frame']>=start)
final=verify.state(out/f'frame-{captures[-1]:04}.ram',l)
result=dict(contract='ENG3-B-v1',area=area,variant=variant,length=length,physical_waveform=wave,observations=len(obs),capture=capture,expected_requests=oracle,actual_actions=actual,legal_consumed_prefix=legal_prefix,images=images,queue_frame_sampled_peak=peak,queue_capacity=127,final=final,status='FAIL' if any(i['gate']=='FAIL' for i in images) or final['overflow'] else 'NOT_QUALIFIED',scope='Achievable whole-PAL external waveform, two images for R+F plus walk U/D. Native early images are measured; truncated consumer tail is not claimed complete.',artifact=json.loads((out/'artifact.json').read_text()))
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('pressure',area,length,result['status'],'peak',peak,'overflow',final['overflow'],'max measured',max(i['full_interval_pal'][1] for i in images),flush=True)
