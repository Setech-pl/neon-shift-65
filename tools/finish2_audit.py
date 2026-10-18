#!/usr/bin/env python3
"""Packed-media, complete-raster, preservation, memory and timing RC2 audit."""
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from art_final_audit import memory,dl_info
from recovery1_audit import extract,sector
from product1_gauntlet import setup
from product1_fix1_review import sections,live,animations
from finish2_probe import STAGES
import verify

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/finish2';BUILD=ROOT/'build/finish2/final';BEFORE=ROOT/'build/finish1/rc1'
PAL=35568;FPS=49.8607597;HZ=PAL*FPS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def rows(p):return list(csv.DictReader(p.open()))

def measure(run):
    data=rows(run/'timeline.csv');sio=rows(run/'sio.csv')
    main=next(int(r['clock']) for r in data if r['event']=='0' and r['edge']=='0')
    pairs=[];entry={}
    for r in data:
        t=int(r['clock']);e=int(r['event'])
        if t<main or e>=len(STAGES):continue
        if r['edge']=='0':entry[e]=t
        elif e in entry:
            a=entry.pop(e);io=sum(max(0,min(t,int(q['end']))-max(a,int(q['begin']))) for q in sio)
            pairs.append(dict(stage=STAGES[e],begin=a,end=t,elapsed_clocks=t-a,SIO_clocks=io,
                              non_IO_clocks=t-a-io,elapsed_s=(t-a)/HZ,SIO_s=io/HZ,non_IO_s=(t-a-io)/HZ))
    bootio=sum(max(0,min(main,int(q['end']))-int(q['begin'])) for q in sio if int(q['begin'])<main)
    return dict(run=str(run.relative_to(ROOT)),main_entry_s=main/HZ,boot_SIO_s=bootio/HZ,
                boot_non_IO_including_splash_s=(main-bootio)/HZ,stages=pairs,
                SIO_calls=len(sio),successful_SIO_calls=sum(q['status']=='1' for q in sio))

def dli_cost(run):
    groups=defaultdict(list);sums=defaultdict(int);counts=defaultdict(int)
    states={int(r['frame']):r for r in rows(run/'frame-schedule.csv')}
    for r in rows(run/'cpu-exclusive.csv'):
        if r['index']!='10':continue
        f=int(r['frame']);s=states.get(f,{})
        kind='loading' if s.get('loading')=='1' else 'menu' if s.get('phase')=='0' else 'game'
        groups[kind].append((int(r['elapsed']),int(r['cpu'])))
        sums[kind,f]+=int(r['elapsed']);counts[kind,f]+=1
    return {kind:dict(samples=len(v),elapsed_min=min(x[0] for x in v),elapsed_max=max(x[0] for x in v),
                 CPU_min=min(x[1] for x in v),CPU_max=max(x[1] for x in v),
                 max_sum_entry_to_label_per_frame=max(s for (k,f),s in sums.items() if k==kind),
                 max_interrupts_per_frame=max(s for (k,f),s in counts.items() if k==kind)) for kind,v in groups.items()}

def main():
    pre=json.loads((DOC/'preflight.json').read_text())
    assert pre['HEAD'].startswith('ea4f415')
    assert sha(ROOT/'assets/levels/camp2-b/campaign.json')==pre['campaign_sha256']
    assert all(sha(ROOT/p)==h for p,h in pre['protected'].items())
    assert sha(Path.home()/'.atari800.cfg')==pre['owner_config_sha256']
    disk=extract(BUILD/'candidate.atr');levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
    image=(BUILD/'candidate.atr').read_bytes();old=(BEFORE/'candidate.atr').read_bytes()
    assert image==(ROOT/'build/finish2/rebuild-final/candidate.atr').read_bytes()
    assert sector(image,1000)==sector(old,1000)
    run=BUILD/'campaign-full';prior=BEFORE/'campaign-full';labs=setup(BUILD);oldlabs=setup(BEFORE)
    assert (run/'emulator.cfg').read_bytes()==(prior/'emulator.cfg').read_bytes()
    assert gzip.decompress((run/'input.gz').read_bytes())==gzip.decompress((prior/'input.gz').read_bytes())
    campaign=json.loads((run/'campaign-result.json').read_text());previous=json.loads((prior/'campaign-result.json').read_text())
    assert campaign['status']=='PASS' and len(campaign['levels'])==60
    free=[124]*5;records=[];pixels=0
    for n,(level,packed,played,before_played) in enumerate(zip(levels,disk['levels'],campaign['levels'],previous['levels'])):
        assert packed['rows']==level['rows'] and packed['area']==level['area'] and packed['name']==level['name']
        assert sector(image,1100+n*70)==sector(old,1100+n*70)
        sec=sections(image,n);oldsec=sections(old,n)
        assert sec[0x9de0][:8]==oldsec[0x9de0][:8] and sec[0x9de0][536:]==oldsec[0x9de0][536:]
        assert [a[:3] for a in animations(sec)]==[a[:3] for a in animations(oldsec)]
        bpath=f"art-area-{level['area']}/level-{n+1:02}/scene-0-banks.json"
        banks=json.loads((BUILD/bpath).read_text());beforebanks=json.loads((BEFORE/bpath).read_text())
        assert banks['devices']==beforebanks['devices']
        for i,b in enumerate(banks['banks']):
            assert b['used']<=128 and b['dynamic_reserved']==4 and not b['conflicts'];free[i]=min(free[i],b['free'])
        w,h=level['visual_size']
        for y in range(8):
            for x in range(16):
                if x<w and y<h:continue
                assert level['rows'][y][x]=='#'
                for q in range(4):
                    pos=(5+y*2+q//2)*40+4+x*2+q%2
                    assert sec[0x1400][(y*20+x)*4+q]==sec[0x9800][pos-80]
        initial=played['frame']-played['moves']*8-15
        assert initial==before_played['frame']-before_played['moves']*8-15
        for f in (initial,played['frame']):
            pixels+=live(run,f,labs,sec)['pixels']
            a=verify.state(run/f'frame-{f:04}.ram',labs);b=verify.state(prior/f'frame-{f:04}.ram',oldlabs)
            assert all(a[k]==b[k] for k in ('phase','scene','player','boxes','moves','pushes','undo'))
        dl=dl_info((run/f'raster-{initial:04}.ram').read_bytes(),labs)
        assert dl==dl_info((prior/f'raster-{initial:04}.ram').read_bytes(),oldlabs)
        records.append(dict(level=n+1,visual_size=[w,h],initial_frame=initial,solved_frame=played['frame'],status='PASS'))
    changed=[]
    for p in (BUILD/'source').iterdir():
        b=BEFORE/'source'/p.name
        if p.is_file() and b.is_file() and p.suffix not in ('.pyc','.o') and p.read_bytes()!=b.read_bytes():changed.append(p.name)
    assert sorted(changed)==['display.c','hardware.s','loading.s','loading_art.py','product1_runtime.py'],changed
    def handler(b):
        s=(b/'source/hardware.s').read_text();return s[s.index('native_dli:\n'):s.index('; Only ISR owns queue producer')]
    assert handler(BUILD)==handler(BEFORE)
    mem={};test_disks=[]
    for name in ('final','test-1','test-16','test-31','test-46'):
        b=ROOT/'build/finish2'/name;mem[name]=memory(b)
        packed=extract(b/'candidate.atr');assert [l['rows'] for l in packed['levels']]==[l['rows'] for l in levels]
        data=(b/'candidate.atr').read_bytes()
        assert sector(data,8100,2)==bytes(256)
        assert sector(data,1000)==sector(image,1000)
        for n in range(60):assert sector(data,1100+n*70,70)==sector(image,1100+n*70,70)
        test_disks.append(dict(build=name,sha256=sha(b/'candidate.atr'),bytes=len(data),all_campaign_sectors_identical=True))
    # All instruction-bearing movement/input/publication/save sources in the
    # normal RC2 are unchanged, including the stacks' linker configuration.
    native=json.loads((BUILD/'native-campaign/result.json').read_text());assert native['status']=='PASS'
    runtime=json.loads((DOC/'runtime.json').read_text());assert runtime['status']=='PASS' and len(runtime['tests'])==24
    eng4=json.loads((BUILD/'eng4/eng4-result.json').read_text())
    assert [a['action'] for a in eng4['accepted_actions']]==list('RZRRZ')
    assert eng4['exactly_one_ordered_full_image_per_accepted_action']
    assert eng4['maxima']['external_to_accept_pal']<=6 and eng4['maxima']['accept_to_full_pal']<=4 and eng4['maxima']['external_to_full_pal']<=10
    timings=[json.loads(p.read_text()) for name in mem for p in (ROOT/'build/finish2'/name).glob('*/timing.json')]
    assert all(t['csp_outside_samples']==0 for t in timings)
    observed=dict(C_stack_peak=max(t['c_stack_sample_peak'] for t in timings),HW_stack_peak=max(t['hardware_stack_observed_peak'] for t in timings),DLI_entry_to_label_max=max(t['isr_max_clocks'][2] for t in timings))
    loading={}
    for label,b,names in (('before',BEFORE,('finish2-before-patch','finish2-before-stock')),('after',BUILD,('presentation-patch','presentation-stock'))):
        loading[label]={mode:measure(b/name) for mode,name in zip(('patch','stock'),names)}
    dump(DOC/'loading.json',dict(clock=f'ANTIC_CPU_CLOCK; 35568/frame; Atari800_FPS_PAL={FPS} from emulator src/atari.h; seconds=clocks/{HZ}',
         separation='SIOV entry to return measured per read; non-I/O is elapsed remainder including CRC/validation/render/VBI/DMA, not exclusive CPU instructions',
         optimizations='No disk/fast-loader optimization; only compact equivalent palette validation/presentation setup for RAM budget',measurements=loading))
    costs={name:dli_cost(BUILD/name) for name in ('presentation-patch','presentation-stock','campaign-full')}
    dump(DOC/'verification.json',dict(status='PASS',base=pre['HEAD'],campaign_sha256=pre['campaign_sha256'],campaign_id=disk['campaign_id'],
         levels=records,pixel_comparisons=pixels,bank_free_minima=free,changed_generated_sources=changed,
         native_DLI_handler_unchanged=True,gameplay_display_lists_and_palettes_identical=True,
         memory=mem,before_memory=memory(BEFORE),observed=observed,DLI=costs,
         DLI_unit='Entry at first PHA to _dli_end immediately before PLA/TAX/PLA/RTI; elapsed ANTIC clocks include WSYNC and DMA. Tail16 CPU cycles and hardware/OS NMI dispatch excluded. CPU columns exclude stalls.',
         disks=test_disks,clean_rebuild_identical=True,protected_files_unchanged=len(pre['protected']),owner_config_unchanged=True,
         ENG4=eng4['maxima'],native_undo=native,runtime_probes=24,visual='OWNER_PENDING',hardware='NOT_RUN',independent_reviewer='NOT_RUN; separate oracles by same agent'))
    dump(DOC/'packed-levels.json',disk)
    print('PASS RC2 audit',pixels,'pixels, fonts',free,'observed',observed,flush=True)

if __name__=='__main__':main()
