# UX1 adaptation: same external phase/gap,500-PAL cold-start prelude, real ATR boot.
"""Common-clock external order, full gs/ring audit, actual displayed images.

Preserve requested-order failures. Classify an unresolved sampler separately
only when the captured instruction log contains no completed intermediate
snapshot. Expected game states come from shared C, never from candidate PNG.
"""
import concurrent.futures,csv,hashlib,json,os,subprocess,sys
from observed_oracle import transactions,expected,runtime_read_pcs,VERSION
from pathlib import Path
B=Path(os.environ['NEON_A5C_BUILD']);W=Path(os.environ.get('A5C_RUN_ROOT','build/renderer-a5c/reproduction'));W.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path('experiments/renderer-a5c').resolve()))
import gauntlet,verify,fetch_oracle,pixel_fast,turbo_run,action_images
from emulator_smoke import run as native_run
from m1_check import png
from compile import arrays
PAL=35568;F640=40511952;PINS=dict(R=(7,1,7),U=(14,1,7),D=(13,1,7),Z=(15,0,7),S=(15,1,6))
def rows(p):
 return [{k:(v if k=='gs_hex' else int(v)) for k,v in r.items()} for r in csv.DictReader(Path(p).open())]
def state(hexbytes):
 b=bytes.fromhex(hexbytes)
 return dict(player=list(b[762:764]),boxes=[list(b[764+i*2:766+i*2]) for i in range(b[784])],moves=int.from_bytes(b[785:789],'little'),pushes=int.from_bytes(b[789:793],'little'))
def one(q):
 name,pattern,tfirst,gap,prefix,variant=q
 out=W/name;assert not out.exists(),name
 out.mkdir();second=tfirst+gap
 # Keep the first pins when the second independent control is pressed.
 a=PINS[pattern[0]];b=PINS[pattern[1]]
 combined=(b[0] if b[0]!=15 else a[0],min(a[1],b[1]),a[2]&b[2])
 schedule=json.loads(os.environ['ENG3_WAVEFORM_JSON']) if 'ENG3_WAVEFORM_JSON' in os.environ else [(tfirst,*a),(second,*combined),(int(os.environ.get('A5C_RELEASE_CLOCK',max(tfirst,second)+PAL)),*PINS.get('NONE',(15,1,7)))]
 (out/'pins.csv').write_text(''.join(','.join(map(str,e))+'\n' for e in schedule))
 (out/'requested.json').write_text(json.dumps(dict(pattern=pattern,tfirst=tfirst,gap=gap,prefix=prefix,variant=variant,external_events=schedule,rule='Device read precedes external transition at equal cycle (original A4 frame-boundary ordering)'),indent=2)+'\n')
 os.environ['ENG2_BUS_RANGE']='1140,1148'
 os.environ['NSQ_PIN_SCHEDULE']=str((out/'pins.csv').resolve())
 os.environ.pop('NSQ_LATE_INPUT',None)
 os.environ['NEON_A5B_OBSERVER']=str(Path('build/eng3-observed-input-3pal/observer/src/atari800').resolve())
 os.environ['NSQ_ACTION_AUDIT']='1139,1148';os.environ['NSQ_INPUT_AUDIT']='1140,1148';os.environ['NSQ_FETCH_RANGE']='1139,1148'
 l=verify.labels(B/(variant+'.lbl'))
 names=['_game_step','_undo_pop','_input_read','_input_tick','_publish_now','publish_update','_foreground_publication_end','_gs','_count','_head','_input_head','_publish_pending','_poll_ready','_input_tail','_poll_stick','_poll_trigger','_poll_console']
 os.environ['NSQ_ACTION_ADDRS']=','.join(f'{l.get(n,0):04x}' for n in names)
 os.environ['NSQ_INPUT_AUDIT_ADDRS']=','.join(f'{l.get(n,0):04x}' for n in ['_poll_stick','_poll_trigger','_poll_console','_poll_last_stick','_poll_last_trigger','_poll_last_console','_input_head','_input_tail','_count','_head','_publish_pending','_poll_ready'])
 verify.pixel_reference=pixel_fast.pixel;gauntlet.check=fetch_oracle.check
 def atr_run(name,*args,**kwargs):
  kwargs['boot']=True
  return native_run(str(out.relative_to('build')),*args,**kwargs)
 gauntlet.run=atr_run
 events=[(700,700,dict(fire=0))]
 if variant=='candidate':events.extend([(900,900,dict(consol=6)),(920,920,dict(stick=7)),(940,940,dict(consol=3))])
 if prefix:events.append((1130 if '-prelude1130' in name else 1100,1130 if '-prelude1130' in name else 1100,dict(stick=7)))
 gauntlet.probe(name,events,list(range(1139,1149)),1175,variant=variant)
 (out/'action-symbols.json').write_text(json.dumps(names,indent=2)+'\n')
 tr=rows(out/'action-state.csv');actions=[];selected=None;dispatch=[]
 for r in tr:
  if r['event']==2 and r['edge']==1:
   selected=r['a']
   if r['clock']>=tfirst and selected:dispatch.append(dict(action=selected,clock=r['clock']))
  if r['event'] in (0,1) and r['edge']==1 and r['clock']>=tfirst:
   c='Z' if r['event']==1 else {1:'U',2:'D',3:'L',4:'R'}[selected]
   actions.append(dict(action=c,clock=r['clock'],accepted=r['a'],undo=r['count'],head=r['head'],state=state(r['gs_hex'])))
 bus=rows(out/'device-reads.csv')
 pcs=runtime_read_pcs(B/(variant+'.xex'))
 observations,capture=transactions(bus,pcs)
 # Verify actual non-peek return against independent waveform, at its own query clock.
 mismatch=[]
 for o in observations:
  for query in o['queries']:
   pins=(15,1,7)
   for edge in schedule:
    if edge[0]<query['clock']:pins=edge[1:]
   index=(0xd300,0xd010,0xd01f).index(query['address'])
   if query['value']!=pins[index]:mismatch.append(query)
 assert not mismatch,('query/waveform mismatch',name,mismatch)
 levelrows=json.loads((B/'levels.json').read_text())['levels'][1]['rows']
 sys.path.insert(0,'experiments/art3-contextual-decoration-review')
 from floor_restore import packages
 from observed_oracle import board_matches
 sections=packages((B/(variant+'.atr')).read_bytes())[1]
 oracle=expected(observations,levelrows,schedule,prefix,0 if variant=='candidate' else 3999999999)
 game_requests=[x for x in oracle if x['action']!='S']
 order=len(actions)==len(game_requests) and all(a['action']==e['action'] for a,e in zip(actions,game_requests))
 legality=order and all(all(a[k]==e[k] for k in ['accepted','undo','state']) for a,e in zip(actions,game_requests))
 accepted=[e for e in game_requests if e['accepted']]
 lastvisible=1138;images=[];missing=[]
 from observed_oracle import Game
 initial=Game(levelrows,0 if variant=='candidate' else 3999999999)
 for c in prefix:initial.request(c)
 previous=initial.player;boxes=initial.boxes
 clock={r['frame']:r['clock'] for r in rows(out/'input-clock.csv')}
 for e in accepted:
  match=[]
  for f in range(max(1140,lastvisible+1),1149):
   observed=out/'fetch-oracle'/f'raster-{f:04}.ram'
   if observed.exists() and board_matches(observed.read_bytes(),e['state'],levelrows,sections):match.append(f)
  if not match:
   missing.append(e);continue
  f=match[0];im,pal=png(out/f'native-{f:04}.png');old,op=png(out/f'native-{max(1139,lastvisible):04}.png')
  bx,by=20-len(levelrows[0]),13-len(levelrows);px,py=e['state']['player'];x0=8+(bx+2*px)*8;y0=24+(by+2*py)*8
  changed=[y for y in range(y0,y0+16) for x in range(x0,x0+16) if pal[im[y][x]]!=op[old[y][x]]]
  if not changed:missing.append(dict(**e,reason='no native changed robot pixel'));continue
  affected=[previous,e['state']['player']]+[x for pair in zip(boxes,e['state']['boxes']) if pair[0]!=pair[1] for x in pair]
  upper=clock[f]+(24+(by+2*max(x[1] for x in affected))*8+16+8)*114+8-e['t0']
  first=clock[f]+(min(changed)+9)*114+8-e['t0']
  images.append(dict(action=e['action'],observation=e['observation'],t0=e['t0'],visible_frame=f,first_interval_pal=[(first-130)/PAL,first/PAL],full_interval_pal=[(upper-130)/PAL,upper/PAL],gate='PASS' if max(first,upper)<=3*PAL else 'FAIL'))
  lastvisible=f;previous=e['state']['player'];boxes=e['state']['boxes']
 pause_frames=[]
 if any(e['action']=='S' for e in oracle):
  font=arrays()['menu_font']
  def pause_native(f):
   im,pal=png(out/f'native-{f:04}.png')
   for n,c in enumerate('SHIFT PAUSED'):
    glyph=ord(c)-64 if c!=' ' else 0
    for yy,v in enumerate(font[glyph*8:glyph*8+8]):
     for xx in range(8):
      if pal[im[64+yy][120+n*8+xx]]!=pal[14 if v&(128>>xx) else 0]:return False
   return True
  pause_frames=[f for f in range(1140,1149) if pause_native(f)]
 pause_order=not any(e['action']=='S' for e in oracle) or bool(pause_frames and all(i['visible_frame']<pause_frames[0] for i in images) and not missing)
 final=verify.state(out/'frame-1148.ram',l)
 gates=dict(observed_order='PASS' if order else 'FAIL',legality_history_counters='PASS' if legality else 'FAIL',separate_images='FAIL' if missing else 'PASS',latency_3_3='PASS' if not missing and all(i['gate']=='PASS' for i in images) else 'FAIL',before_pause='PASS' if pause_order else 'FAIL',overflow='FAIL' if final['overflow'] or final['publication_overflow'] else 'PASS')
 result=dict(contract='ENG3-B-v1',oracle=VERSION,status='PASS' if all(v=='PASS' for v in gates.values()) else 'FAIL',gates=gates,artifact=json.loads((out/'artifact.json').read_text()),physical_requested=pattern,physical_actual=''.join(a['action'] for a in actions),actions=actions,expected_requests=oracle,images=images,missing_images=missing,pause_frames=pause_frames,final=final,external_events=schedule,capture=capture,observations=observations,dispatch=dispatch,full_native=fetch_oracle.check.__doc__)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,result['status'],gates,flush=True)

if __name__=='__main__':
 assert sys.argv[1]=='--one'
 one(json.loads(sys.argv[2]))
