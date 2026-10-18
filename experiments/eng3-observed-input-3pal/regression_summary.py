"""Explicit semantic repeat/button, START/config and idle-attract assertions."""
import sys,json,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,'experiments/renderer-a5c');from verify import labels,state
B=Path('build/eng3-observed-input-3pal');result=[]
for a in range(1,5):
 root=B/f'area-{a}';p=root/'game-accepted-repeat';l=labels(p/'candidate.lbl')
 # Independent contract:41frames held direction, delay14/repeat5 ->7 actions;
 # FIRE is edge-only ->one undo even when held41frames.
 expected=[json.loads(s) for s in subprocess.check_output([str(root/'logic-oracle'),'1','RRRRRRRZ','3999999999'],text=True).splitlines()]
 observed=[];last=state(p/'frame-0990.ram',l)
 for f in range(991,1160):
  s=state(p/f'frame-{f:04}.ram',l)
  if s['moves']!=last['moves']:observed.append(dict(frame=f,state=s));last=s
 assert len(observed)==len(expected)==8
 for e,o in zip(expected,observed):assert all(o['state'][k]==v for k,v in e.items()),(a,e,o)
 q=root/'game-accepted-small-ui';l=labels(q/'candidate.lbl');phases=[]
 for f,want in [(950,1),(1020,3),(1100,3),(1300,1),(1410,3),(1440,7),(1470,7),(1500,7),(1530,3),(1580,1),(1620,1)]:
  b=(q/f'frame-{f:04}.ram').read_bytes();got=b[l['_phase']];assert got==want,(a,f,got,want);phases.append(dict(frame=f,phase=got))
 q=root/'game-accepted-attract';idle=[]
 for f in [680,32000,32840,33000,36000]:
  b=(q/f'frame-{f:04}.ram').read_bytes();assert list(b[0x4d:0x50])==[0,254,0],(a,f,list(b[0x4d:0x50]));idle.append(dict(frame=f,ATRACT=b[0x4d],DRKMSK=b[0x4e],COLRSH=b[0x4f]))
 m=json.loads((root/'game-measurements.json').read_text());assert all(v['schedule']['status']=='PASS' for v in m.values())
 audio=json.loads((root/'native-film/audio-validation.json').read_text());assert audio['status']=='PASS'
 result.append(dict(area=a,ATR=hashlib.sha256((root/'candidate.atr').read_bytes()).hexdigest(),repeat=dict(status='PASS',held_R_actions=7,held_FIRE_actions=1,observed=observed),START_config_resume=dict(status='PASS',phases=phases),OS_attract=dict(status='PASS',run_frames=36600,samples=idle),audio=dict(status='MACHINE_PASS',listening='NOT_RUN',schedule={k:v['schedule'] for k,v in m.items()},PCM=audio)))
(B/'regression-summary.json').write_text(json.dumps(dict(status='PASS',areas=result),indent=2)+'\n');print('PASS repeat7R/1undo,START/config/resume,idleOS-attract,audio machine checks all4areas')
