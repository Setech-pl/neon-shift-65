"""Per-area linker allocations, disk packages, finite CPU/stacks and phases."""
import json,re,csv,struct,hashlib
from pathlib import Path
B=Path('build/eng3-observed-input-3pal')
def labels(p):return {m[2]:int(m[1],16) for m in re.finditer(r'al (\w+) \.([\w]+)',p.read_text())}
def union(regions):
 spans=[]
 for n,a,z in sorted(regions,key=lambda q:q[1]):
  if spans and a<=spans[-1][1]:spans[-1][1]=max(spans[-1][1],z)
  else:spans.append([a,z])
 return dict(bytes=sum(z-a for a,z in spans),spans=spans,regions=[dict(name=n,start=a,end_exclusive=z,bytes=z-a) for n,a,z in regions])
def r(n,a,size):return(n,a,a+size)
def ambient(root):
 checks=[]
 for name in ['replay','hud','repeat','dock']:
  out=root/('game-accepted-'+name);l=labels(out/'candidate.lbl');pairs=0;glyphs=0;updates=0;last=None
  for p in sorted(out.glob('raster-*.ram')):
   f=int(p.stem.split('-')[-1]);ram=p.read_bytes()
   if not ram[l['_ambient_active']]:last=None;continue
   count=ram[0x9de4];records=[struct.unpack_from('<HBB4B',ram,0x9e60+i*8) for i in range(count)]
   actual=out/'fetch-oracle'/p.name
   if actual.exists():
    fetched=actual.read_bytes()
    for i,(a,period,phase,*codes) in enumerate(records):
     assert fetched[a]==codes[ram[l['anim_phases']+i]>>5],(root,name,f,i,'phase vs actual ANTIC screen')
     glyphs+=1
   if last and f==last[0]+1:
    prior=last[1]
    for i,(a,period,phase,*codes) in enumerate(records):
     t=prior[l['anim_ticks']+i];ph=prior[l['anim_phases']+i]
     assert ram[l['anim_ticks']+i]==(t+1)%period,(root,name,f,i,'ambient starvation')
     assert ram[l['anim_phases']+i]==(ph+(32 if t+1>=period else 0))&96,(root,name,f,i,'shared/lost phase')
     updates+=int(t+1>=period)
    pairs+=1
   last=(f,ram)
  assert pairs and glyphs
  checks.append(dict(fixture=name,status='PASS',adjacent_active_pairs=pairs,actual_ANTIC_phase_checks=glyphs,independent_phase_updates=updates))
 return dict(status='PASS',method='Unchanged phase/tick arrays in adjacent active read-only raster snapshots; exact per-descriptor progression and actual ANTIC screen codes. No fitted phase offset, no PNG oracle substitution.',checks=checks)
def one(area):
 root=B/f'area-{area}';l=labels(root/'candidate.lbl');variants=[]
 for base in [root,root/'open']:
  for p in sorted(base.glob('*.lbl')):
   q=labels(p)
   if '__BSS_RUN__' not in q:continue
   variants.append(dict(variant=str(p.relative_to(root)),MAIN_used=q['__BSS_RUN__']+q['__BSS_SIZE__']-8192,MAIN_free=32768-q['__BSS_RUN__']-q['__BSS_SIZE__'],LOW_used=q['__LOADBSS_RUN__']+q['__LOADBSS_SIZE__']-1536,LOW_free=5120-q['__LOADBSS_RUN__']-q['__LOADBSS_SIZE__'],ZP_used=q['__ZP_LAST__']-130,ZP_free=256-q['__ZP_LAST__']))
 banks={}
 for fixture,base in [('obstacles',root),('open',root/'open')]:
  for scene in range(3):
   v=json.loads((base/f'scene-{scene}-banks.json').read_text());banks[f'{fixture}/scene-{scene}']=dict(geometry=v['geometry'],animations=v['animations'],banks=[{k:b[k] for k in ['bank','address','absolute_rows','static_unique','dynamic_reserved','used','free','conflicts']} for b in v['banks']])
 shared=[r('HW stack full reservation',0x100,256),r('status',0x1720,224),r('loader art',0xba00,1280),r('loader DL',0xbf00,128),r('boot sector buffer',0xbf80,128),('MAIN',8192,l['__BSS_RUN__']+l['__BSS_SIZE__']),('LOW',1536,l['__LOADBSS_RUN__']+l['__LOADBSS_SIZE__']),('ZP',130,l['__ZP_LAST__']),r('COMMON',0x9c80,352),r('C stack full reservation',0x8000,2048),r('music reserved',0x1800,2048),r('sector buffer',0x9c00,128),r('header',0x9b70,144)]
 menu=[r('screen',0x8800,960),r('font',0x8c00,1024),r('menu DL incl dead-theme overlay',0x9f60,154),r('room',0xa000,3200),r('title',0xb000,800),r('footer',0xb400,1200)]
 game=[r('composition',0x1400,800),r('screen',0x8800,960),r('bank0',0x8c00,1024),r('HUD',0x9000,1024),r('HUD staging',0x9400,408),r('base',0x9800,880),r('descriptor',0x9de0,384),r('DL',0x9f60,152),r('active theme metadata',0x9ff8,8),r('banks1..4',0xa000,4096),r('robot source',0xb160,1280),r('candidate state',0xb680,793)]
 stages={k:union(shared+v) for k,v in [('menu',menu),('level_transition_conservative_old_menu_plus_game',menu+game+[r('loader label',0x9100,320)]),('active_gameplay_pause_config_error',game)]}
 packages=json.loads((root/'packages.json').read_text());atr=json.loads((root/'candidate-atr.json').read_text());allocated=3+1+atr['program_sectors'];disk=[]
 for p,start in zip([p for p in packages if p['kind']<=5],atr['package_starts']):
  sectors=(p['bytes']+127)//128;allocated+=sectors
  disk.append(dict(name=p['name'],start=start,sectors=sectors,raw=p['raw'],encoded=p['bytes'],encoding='NSRQ v2 RAW sections +144B CRC header'))
 profiles=[];max_cpu={};schedule={}
 for out in sorted(root.glob('game-accepted-*')):
  if not (out/'timing.json').exists():continue
  timing=json.loads((out/'timing.json').read_text());profiles.append(dict(fixture=out.name,**timing))
  for row in csv.DictReader((out/'cpu-exclusive.csv').open()):
   key=int(row['index']);d=max_cpu.setdefault(key,dict(samples=0,max_cpu=0,max_elapsed=0));d['samples']+=1;d['max_cpu']=max(d['max_cpu'],int(row['cpu']));d['max_elapsed']=max(d['max_elapsed'],int(row['elapsed']))
  entries=[{k:int(v) for k,v in row.items()} for row in csv.DictReader((out/'frame-schedule.csv').open())]
  pairs=[(a,b) for a,b in zip(entries,entries[1:]) if a['frame']>=680 and not a['loading'] and not b['loading']]
  bad=[a['frame'] for a,b in pairs if (b['audio_calls']-a['audio_calls'])%256!=1 or b['skctl']!=3 or b['audctl']!=0]
  assert not bad,(area,out,'audio scheduler',bad)
  schedule[out.name]=dict(status='PASS',active_pairs=len(pairs),bad=bad)
 names=['HUD request','game step','undo','dirty cells','robot/dock prepare','publication','music','package load','native VBI','ambient','native DLI']
 cpu=[dict(name=names[k],**d) for k,d in sorted(max_cpu.items())]
 stacks=dict(C_reserved=2048,HW_reserved=256,observed_C_peak=max(p['c_stack_sample_peak'] for p in profiles),observed_HW_peak=max(p['hardware_stack_observed_peak'] for p in profiles),CSP_outside=sum(p['csp_outside_samples'] for p in profiles),profiles=len(profiles),classification='Finite observations; not a formal stack or CPU WCET. Full reservations retained.')
 phase=ambient(root)
 active=stages['active_gameplay_pause_config_error']['bytes'];peak=max(s['bytes'] for s in stages.values())
 d=dict(area=area,ATR_SHA256=hashlib.sha256((root/'candidate.atr').read_bytes()).hexdigest(),variants=variants,banks=banks,active_pack=dict(raw_transfer=8624,encoded=8768,banks=5120,robot=1280,base=880,composition=800,descriptor_transfer=544,live_descriptor=384,theme=8,staging_sector=128,staging_header=144),RAM=dict(active_reserved_union=active,transition_peak_reserved_union=peak,lifetimes=stages),disk=dict(bytes=(root/'candidate.atr').stat().st_size,total_sectors=8192,allocated=allocated,unallocated=8192-allocated,packages=disk,program=atr),CPU=dict(method='Per-area actual procedure-label exclusive CPU cycles; elapsed includes DMA/WSYNC/ISR for foreground; inclusive and exclusive are not summed. Emulator PAL1773447Hz/35568cycles.',procedures=cpu),stacks=stacks,audio_schedule=schedule,ambient=phase,metadata_overlay='Gameplay DL152B $9f60..$9ff7; THEMERAM8B $9ff8..$9fff. Menu DL154B overlaps first2B of dead THEMERAM; resume/prepare always reloads validated scene before gameplay. Loader descriptor544B overwrites inactive DL while DMA is stopped. No extra area remains resident.')
 (root/'resource-measurements.json').write_text(json.dumps(d,indent=2)+'\n');print(area,'active',active,'peak',peak,'stacks',stacks,'ambient',phase['status'],flush=True)
 return d
if __name__=='__main__':
 result=[one(a) for a in range(1,5)];(B/'resource-measurements.json').write_text(json.dumps(result,indent=2)+'\n')
