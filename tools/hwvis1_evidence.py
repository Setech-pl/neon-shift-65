#!/usr/bin/env python3
"""Freeze native transition frames and read-only traces, excluding RAM/ROM/config."""
import csv,gzip,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
from art_final_audit import memory
D=Path('docs/hwvis1');BASE=Path('build/hwvis1');E=D/'evidence';E.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runs=[Path('build/release1/final/hwvis-before'),Path('build/release1/final/hwvis-before-handover'),BASE/'final/hwvis-after',BASE/'final/hwvis-after-handover']+[BASE/f'final/boundary-{n}' for n in (15,30,45,60)]
records=[]
with zipfile.ZipFile(E/'native-transitions.zip','w',zipfile.ZIP_DEFLATED) as z:
    for run in runs:
        for p in sorted(run.glob('native-*.png')):z.write(p,f'{run.name}/{p.name}')
        for name in ('hwvis-dli.csv','hwvis-frames.csv','sio.csv','timeline.csv','input.gz','hwvis-effective.json'):
            p=run/name
            if p.exists():z.write(p,f'{run.name}/{name}')
        a=json.loads((run/'artifact.json').read_text());records.append(dict(run=run.name,ATR=a['ATR'],effective=json.loads((run/'hwvis-effective.json').read_text()),frames=[int(p.stem.split('-')[1]) for p in sorted(run.glob('native-*.png'))]))
    z.writestr('manifest.json',json.dumps(records,indent=2))
for label,run in [('before',runs[0]),('after',runs[2])]:
    for screen,frame in [('menu',2750),('loader',3500),('HUD',4100)]:
        shutil.copyfile(run/f'native-{frame:04}.png',E/f'{screen}-{label}.png')
    frames=list(csv.DictReader((run/'hwvis-frames.csv').open()));dli=list(csv.DictReader((run/'hwvis-dli.csv').open()));loader=[q for q in dli if q['loading']=='1']
    records.append(dict(label=label,loading_DLI=len(loader),loading_max_row=max([int(q['row']) for q in loader],default=None),loading_invalid_phase=sum(int(q['row'])>1 for q in loader),loading_DLI_critical=sum(q['critic']!='0' for q in loader),game_DLI_max=max(int(q['dli']) for q in frames if q['loading']=='0' and q['phase']=='1')))
    # Compare only the static illustration/background, excluding label/progress.
    output=BASE/f'{label}-loader-frames.md5'
    subprocess.run(['ffmpeg','-v','error','-y','-start_number','3210','-i',str(run/'native-%04d.png'),'-frames:v','400','-vf','crop=336:144:0:24','-f','framemd5',str(output)],check=True)
    hashes=[line.rsplit(',',1)[-1].strip() for line in output.read_text().splitlines() if not line.startswith('#')]
    records[-1]['static_loader_400_consecutive_frames_distinct']=len(set(hashes))
    shutil.copyfile(output,E/output.name)
    label_output=BASE/f'{label}-loader-label.md5'
    subprocess.run(['ffmpeg','-v','error','-y','-start_number','3210','-i',str(run/'native-%04d.png'),'-frames:v','400','-vf','crop=336:8:0:176','-f','framemd5',str(label_output)],check=True)
    label_hashes=[line.rsplit(',',1)[-1].strip() for line in label_output.read_text().splitlines() if not line.startswith('#')]
    records[-1]['label_400_consecutive_frames_distinct']=len(set(label_hashes))
    shutil.copyfile(label_output,E/label_output.name)
assert records[-1]['label_400_consecutive_frames_distinct']==1 and records[-2]['label_400_consecutive_frames_distinct']==4
assert records[-1]['loading_DLI']==0 and records[-1]['static_loader_400_consecutive_frames_distinct']==1
# Store result summaries outside historical directories.
for source,name in [(BASE/'final/campaign-stock/campaign-result.json','campaign60.json'),(BASE/'final/fire-tests.json','A01.json'),(BASE/'final/save-faults/result.json','A02.json')]:
    if source.exists():shutil.copyfile(source,D/name)
normal=(BASE/'final/candidate.atr').read_bytes();before=Path('build/release1/final/candidate.atr').read_bytes()
assert all(normal[16+(1100+i*70-1)*128:16+(1170+i*70-1)*128]==before[16+(1100+i*70-1)*128:16+(1170+i*70-1)*128] for i in range(60))
for name in ('campaign.c','main.c','render.s','input.c','move.s','undo-fast.s','phase.s'):
    assert (BASE/'final/source'/name).read_bytes()==(Path('build/release1/final/source')/name).read_bytes(),name
# Native gameplay ISR bytes are source-identical; initialization/menu palette differ.
for marker,end in [('native_dli:', '; Only ISR owns'),('native_vbi:', '_publicatio')]:
    a=(BASE/'final/source/hardware.s').read_text();b=Path('build/release1/final/source/hardware.s').read_text()
    assert a[a.index(marker):a.index(end,a.index(marker))]==b[b.index(marker):b.index(end,b.index(marker))]
mem={n:memory(BASE/n) for n in ('final','test-1','test-16','test-31','test-46')}
stacks={}
for run in (BASE/'final').iterdir():
    p=run/'timing.json'
    if p.exists():
        m=json.loads(p.read_text());assert m['csp_outside_samples']==0,(run,m)
        stacks[run.name]={k:m[k] for k in ('c_stack_sample_peak','hardware_stack_observed_peak','csp_outside_samples')}
checks=dict(status='PASS',normal_sha256=sha(BASE/'final/candidate.atr'),repeat_hashes=[sha(BASE/f'{n}/build/normal/candidate.atr') for n in ('clean-a','clean-b')],campaign_source_sha256=sha(Path('assets/levels/camp2-b/campaign.json')),all_60_board_and_graphics_sectors_unchanged=True,core_sources_unchanged=True,game_DLI_and_VBI_body_unchanged=True,memory=mem,observed_stacks=stacks,transitions=records,evidence_zip=dict(file='evidence/native-transitions.zip',sha256=sha(E/'native-transitions.zip'),bytes=(E/'native-transitions.zip').stat().st_size))
assert len(set(checks['repeat_hashes']+[checks['normal_sha256']]))==1
(D/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print('PASS immutable campaign/resources, ISR bodies, memory/stacks, frame sequences and stable loader')
