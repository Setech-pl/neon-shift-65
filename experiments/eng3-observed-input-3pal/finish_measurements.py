"""Collect completed fresh measurements, with explicit scope and raw hashes."""
from capture_cases import *
import re,shutil,collections
CP=D.parent
profiles=[]
for p in B.rglob('timing.json'):
 if 'focused/' in str(p) or 'adapter' in str(p) or 'frozen-source' in str(p) or not (p.parent/'artifact.json').exists():continue
 profiles.append(dict(path=str(p.relative_to(R)),**json.loads(p.read_text())))
resources=json.loads((B/'resource-measurements.json').read_text());queue=[]
for p in B.glob('area-*/game-accepted-*/frame-schedule.csv'):
 q=[int(r['queue'])&127 for r in csv.DictReader(p.open()) if int(r['frame'])>=680]
 queue.append(dict(path=str(p.relative_to(R)),peak=max(q)))
water=dict(profiles=len(profiles),C_peak=max(d['c_stack_sample_peak'] for d in profiles),HW_peak=max(d['hardware_stack_observed_peak'] for d in profiles),CSP_outside=sum(d['csp_outside_samples'] for d in profiles),C_reserve=2048,HW_reserve=256,queue_frame_sampled_peak=max(q['peak'] for q in queue),queue_capacity=127,queue=queue,maximum_reserved_union=46869,default_active_reserved_union=46437,default_transition_reserved_union=46821,per_byte_simultaneously_live_peak='UNMEASURED: source ownership audit is separate; reservations not relabelled liveness',all_path_WCET='UNRESOLVED',profile_records=profiles)
js(D/'runtime-resources.json',dict(resources=resources,high_water=water))
summary=json.loads((B/'qualification-summary.json').read_text());js(D/'qualification-summary.json',summary)
costs=[];hud=[]
for a in range(1,5):
 p=B/f'area-{a}';m=json.loads((p/'game-measurements.json').read_text())
 for name in ['hud','replay']:
  hud.append(dict(area=a,fixture=name,latency=m[name]['latency'],HUD=m[name]['HUD']))
 for n in ['game-measurements.json','resource-measurements.json','qualification-summary.json','ux2-contracts.json']:
  shutil.copyfile(p/n,CP/f'area-{a}'/n)
 costs.append(dict(area=a,CPU=resources[a-1]['CPU']['procedures'],active_HUD_work={name:{k:m[name]['HUD'][k] for k in ['max_active_work_cpu','max_active_work_elapsed','max_job_cpu','freshness']} for name in ['hud','replay']}))
js(D/'CPU-and-HUD.json',dict(scope='Finite fresh gameplay/replay/HUD/dock/repeat/attract/UI runs. Exclusive CPU and elapsed maxima stay separate; inclusive VBI components are not added twice. No all-path worst-convergence claim.',areas=costs,HUD=hud))
music=[]
for a in range(1,5):
 p=B/f'area-{a}/native-film';l={n:int(v,16) for v,n in re.findall(r'^al (\w+) \.(\w+)',(B/f'area-{a}/candidate.lbl').read_text(),re.M)};active=[];writes=set()
 with tarfile.open(p/'raw.tar.gz','r|gz') as t:
  for member in t:
   if member.name=='register-writes.csv':
    for q in csv.DictReader(line.decode() for line in t.extractfile(member)):
     if int(q['address'])==0xd201 and 0xa2<=int(q['value'])<=0xa6:writes.add(int(q['frame']))
   elif re.fullmatch(r'raster-\d+.ram',member.name):
    ram=t.extractfile(member).read();f=int(member.name[7:-4])
    if ram[l['_display_active']] and ram[l['_music_enabled']] and not ram[l['_asset_loading']] and ram[l['_ambient_active']]:active.append(f)
 assert active and all(f in writes for f in active)
 music.append(dict(area=a,PCM=json.loads((p/'audio-validation.json').read_text()),active_frames=len(active),bass_envelope_every_complete_active_frame='PASS',listening='NOT_RUN'))
js(D/'audio.json',music)
capacity=subprocess.check_output(['sim65',str(B/'capacity-check/test')],text=True);assert 'errors=1' not in capacity
(D/'history-capacities.txt').write_text(capacity)
owner=[]
for a in range(1,5):
 out=subprocess.check_output([sys.executable,str(S/'owner_smoke.py'),'--area',str(a),'--check'],text=True)
 q=json.loads(out);assert '-windowed' in q['command'];owner.append(q)
js(D/'owner-launch-checks.json',dict(runs=owner,agent_visible_emulator_runs=0,owner='NOT_CONFIRMED'))
floor=[json.loads(p.read_text()) for p in (B/'floors/final/floor-walk').glob('*/floor-result.json')];js(D/'floor-results.json',floor)
focused=[json.loads(p.read_text()) for p in (B/'focused-final').glob('*/independent-result.json')];js(D/'focused-results.json',focused)
# Preserve every raw file through per-run lossless archives. Build raw stays local
# (4+GiB), hashes/paths and readable results are checkpointed explicitly.
archives=[]
for p in sorted(B.rglob('raw.tar.gz')):
 archives.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,manifest=str(p.with_name('raw-manifest.json').relative_to(R)),manifest_sha256=sha(p.with_name('raw-manifest.json'))))
js(D/'raw-evidence-manifest.json',dict(archives=archives,archive_count=len(archives),bytes=sum(r['bytes'] for r in archives),storage='Local build/ paths; not embedded as a second multi-GiB copy in Git. Every member hash is in its raw-manifest.json. All original raw bytes retained; adapter failures remain separate.',restore='tar -xzf raw.tar.gz in the corresponding directory; use tarfile.extractfile for selected raw only.'))
print('profiles',len(profiles),'C/HW',water['C_peak'],water['HW_peak'],'raw',len(archives),'musicactive',sum(r['active_frames'] for r in music))
