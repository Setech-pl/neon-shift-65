"""Collect separate B gates; historical results stay in their original files."""
from pathlib import Path
import json,hashlib,collections,shutil
B=Path('build/eng3-observed-input-3pal');D=Path('docs/checkpoints/eng3-observed-input-3pal');E=D/'evidence'
def load(p):return json.loads(Path(p).read_text())
def group(name):
    entries=load(E/(name+'-runs.json'))
    records=entries['runs'] if isinstance(entries,dict) else entries
    data=[load(r['result']) for r in records]
    gates={k:dict(collections.Counter(d['gates'][k] for d in data)) for k in data[0]['gates']}
    images=[dict(area=r['area'],id=r['id'],**i) for r,d in zip(records,data) for i in d['images']]
    return dict(cases=len(data),status_counts=dict(collections.Counter(d['status'] for d in data)),gates=gates,
        max_first=max((i['first_interval_pal'][1] for i in images),default=0),
        max_full=max((i['full_interval_pal'][1] for i in images),default=0),
        worst_full=max(images,key=lambda i:i['full_interval_pal'][1]) if images else None)
matrix={name:group(name) for name in ['matrix','new','pairs','edge-noop']}
pressure=[]
for p in sorted(B.glob('area-*/pressure-*/result.json')):
    d=load(p);images=d['images'];firstfail=next((i for i in images if i['gate']=='FAIL'),None)
    pressure.append(dict(area=d['area'],variant=d.get('variant','carry'),length=d['length'],raw=str(p.parent),status=d['status'],legal_consumed_prefix=d['legal_consumed_prefix'],actual=len(d['actual_actions']),expected_requests=len(d['expected_requests']),observations=d['observations'],peak=d['queue_frame_sampled_peak'],overflows=d['final']['overflow'],first_fail=firstfail,max_first=max(i['first_interval_pal'][1] for i in images if i['first_interval_pal']),max_full=max(i['full_interval_pal'][1] for i in images)))
hud=[];stacks=[];audio=[]
for area in range(1,5):
    root=B/f'area-{area}'
    for name in ['game-measurements.json','resource-measurements.json','ux2-contracts.json']:
        shutil.copyfile(root/name,E/(f'area-{area}-'+name))
    m=load(root/'game-measurements.json')
    for fixture in m:
        latency=m[fixture].get('latency',{})
        if latency: hud.append(dict(area=area,fixture=fixture,max_first=latency.get('max_visible_pal'),max_full=latency.get('max_robot_complete_pal'),max_HUD=latency.get('max_hud_pal'),superseded=latency.get('superseded_hud_requests')))
    for p in root.glob('game-accepted-*/timing.json'):stacks.append(dict(area=area,fixture=p.parent.name,**load(p)))
    audio.append(load(root/'native-film/audio-validation.json'))
phase=load(E/'phase-runs.json')
summary=dict(contract='ENG3-B-v1',engine='FAIL',matrix=matrix,phase_cases=len(phase['runs']),pressure=pressure,HUD=hud,max_HUD=max(x['max_HUD'] for x in hud if x['max_HUD'] is not None),stacks=dict(C_reserved=2048,HW_reserved=256,C_peak=max(x['c_stack_sample_peak'] for x in stacks),HW_peak=max(x['hardware_stack_observed_peak'] for x in stacks),CSP_outside=sum(x['csp_outside_samples'] for x in stacks)),audio=audio,capture_WCET='UNPROVEN all paths; FIFO full produces measured skipped capture',FIFO='FAIL: reachable producer1.5 actions/PAL versus at most1 guarded critical publication/PAL',live_data='Reservations and ownership audit only; global per-byte liveness UNPROVEN',owner='NOT_RUN',listening='NOT_RUN',Atari_SIO2SD='NOT_RUN')
(E/'qualification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(engine=summary['engine'],matrix=matrix,max_HUD=summary['max_HUD'],pressure=pressure,stacks=summary['stacks']),indent=2))
