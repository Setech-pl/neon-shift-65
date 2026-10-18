#!/usr/bin/env python3
"""Bind RC1 to f5df646, actual ATR boards, all live PAL rasters and budgets."""
import gzip
import hashlib
import json
from pathlib import Path
from art_final_audit import memory,dl_info
from recovery1_audit import extract,sector
from product1_gauntlet import setup
from product1_fix1_review import sections,live,animations

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/finish1'
BUILD=ROOT/'build/finish1/rc1'
BEFORE=ROOT/'build/art-final/final'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def main():
    levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
    pre=json.loads((DOC/'preflight.json').read_text())
    assert sha(ROOT/'assets/levels/camp2-b/campaign.json')==pre['campaign_sha256']
    assert sha(BEFORE/'candidate.atr')=='830a7db2e5d7470186e9725bf39a2c64a8eec101d85d460a983506f1b2027c55'
    image=(BUILD/'candidate.atr').read_bytes();old=(BEFORE/'candidate.atr').read_bytes()
    assert image==(ROOT/'build/finish1/rebuild-proof/candidate.atr').read_bytes()
    disk=extract(BUILD/'candidate.atr');assert len(disk['levels'])==60 and disk['campaign_id']=='131c57e2'
    run=BUILD/'campaign-full';prior=BEFORE/'campaign-full'
    replay=json.loads((run/'campaign-result.json').read_text())
    original=json.loads((prior/'campaign-result.json').read_text())
    assert replay['status']=='PASS' and len(replay['levels'])==60
    assert (run/'emulator.cfg').read_bytes()==(prior/'emulator.cfg').read_bytes()
    assert gzip.decompress((run/'input.gz').read_bytes())==gzip.decompress((prior/'input.gz').read_bytes())
    labs=setup(BUILD.relative_to(ROOT));records=[];pixels=0;free=[124]*5;areas=[0]*4;dli=[]
    expected_palettes=((238,154,2,6,0),(238,186,2,6,0),(238,138,2,6,0),(238,58,2,6,0))
    for n,(level,packed,played,before_played) in enumerate(zip(levels,disk['levels'],replay['levels'],original['levels'])):
        assert packed['rows']==level['rows'] and packed['number']==n+1 and packed['area']==level['area'] and packed['name']==level['name']
        assert sector(image,1100+70*n)==sector(old,1100+70*n)
        sec=sections(image,n);previous=sections(old,n)
        assert [a[:3] for a in animations(sec)]==[a[:3] for a in animations(previous)]
        assert sec[0x9de0][:8]==previous[0x9de0][:8]
        assert sec[0x9de0][536:541]==bytes(expected_palettes[level['area']-1])
        banks=json.loads((BUILD/f"art-area-{level['area']}/level-{n+1:02d}/scene-0-banks.json").read_text())
        before_banks=json.loads((BEFORE/f"art-area-{level['area']}/level-{n+1:02d}/scene-0-banks.json").read_text())
        assert banks['devices']==before_banks['devices']
        for i,b in enumerate(banks['banks']):
            assert b['used']<=128 and b['dynamic_reserved']==4 and not b['conflicts']
            free[i]=min(free[i],b['free'])
        w,h=level['visual_size'];padding=0
        for y in range(8):
            for x in range(16):
                if x<w and y<h:continue
                assert level['rows'][y][x]=='#';padding+=1
                for q in range(4):
                    pos=(5+y*2+q//2)*40+4+x*2+q%2
                    assert sec[0x1400][(y*20+x)*4+q]==sec[0x9800][pos-80]
        initial=played['frame']-played['moves']*8-15
        assert initial==before_played['frame']-before_played['moves']*8-15
        for frame in (initial,played['frame']):
            pixels+=live(run,frame,labs,sec)['pixels']
            import verify
            a=verify.state(run/f'frame-{frame:04}.ram',labs)
            b=verify.state(prior/f'frame-{frame:04}.ram',labs)
            assert all(a[k]==b[k] for k in ('phase','scene','player','boxes','moves','pushes','undo'))
        if n in (0,8,15,23,30,38,45,53):
            dl=dl_info((run/f'raster-{initial:04}.ram').read_bytes(),labs)
            assert dl['bytes']==32 and dl['DLI_last_scanlines']==[31,39,71,103,135,167]
            assert dl['raw']==dl_info((prior/f'raster-{initial:04}.ram').read_bytes(),labs)['raw']
            assert dl['table_PF1']==[14]+[expected_palettes[level['area']-1][1]]*5
            assert dl['table_PF2']==[0]+[2]*5
            dli.append(dict(level=n+1,frame=initial,display_list=dl))
        records.append(dict(number=n+1,area=level['area'],visual_size=[w,h],padding_cells=padding,
                            initial_frame=initial,solved_frame=played['frame'],status='PASS'))
    # An exact bound on program changes: only the fourteen palette-table bytes.
    x=(BEFORE/'candidate.xex').read_bytes();y=(BUILD/'candidate.xex').read_bytes()
    diff=[dict(offset=i,before=a,after=b) for i,(a,b) in enumerate(zip(x,y)) if a!=b]
    assert len(x)==len(y) and [d['offset'] for d in diff]==[19880,19881,19882,19883,19885,19886,19887,19889,19890,19891,19892,19893,19894,19895]
    outside=[]
    for i,(a,b) in enumerate(zip(old,image)):
        if a==b:continue
        s=(i-16)//128+1
        if 1101<=s<=5299 and (s-1100)%70:areas[(s-1101)//1050]+=1
        else:outside.append(dict(offset=i,before=a,after=b))
    assert outside==[dict(offset=d['offset']+4531,before=d['before'],after=d['after']) for d in diff]
    assert len(old)==len(image) and (BEFORE/'candidate.lbl').read_bytes()==(BUILD/'candidate.lbl').read_bytes()
    sources=('hardware.s','input.c','main.c','campaign.c','campaign.h','link.cfg','regions.s','move.s','undo-fast.s','phase.s','render.s','validate.c','loader.c','sio.s')
    for name in sources:assert (BEFORE/'source'/name).read_bytes()==(BUILD/'source'/name).read_bytes(),name
    display=(BUILD/'source/display.c').read_text()
    previous=(BEFORE/'source/display.c').read_text()
    assert display==previous.replace('pf1[4]={156,188,76,56},pf2[4]={2,178,66,50},pf0[4]={238,190,78,60},pf3[4]={230,186,74,58}',
                                     'pf1[4]={154,186,138,58},pf2[4]={2,2,2,2},pf0[4]={238,238,238,238},pf3[4]={6,6,6,6}')
    mem=memory(BUILD);assert mem==memory(BEFORE)
    timing=json.loads((run/'timing.json').read_text());old_timing=json.loads((prior/'timing.json').read_text())
    assert timing['csp_outside_samples']==0
    assert timing['isr_max_clocks'][2]<=old_timing['isr_max_clocks'][2]
    assert timing['c_stack_sample_peak']<=mem['C_stack_reserved']
    assert timing['hardware_stack_observed_peak']<256
    saves=json.loads((DOC/'save-results.json').read_text());assert saves['status']=='PASS' and len(saves['tests'])==6
    timings=[json.loads(p.read_text()) for p in BUILD.glob('*/timing.json')]
    assert all(t['csp_outside_samples']==0 for t in timings)
    observed=dict(C_stack_peak=max(t['c_stack_sample_peak'] for t in timings),
                  hardware_stack_peak=max(t['hardware_stack_observed_peak'] for t in timings),
                  DLI_max_elapsed_clocks=max(t['isr_max_clocks'][2] for t in timings))
    preserved=pre['preserved_files']
    assert all((ROOT/p).exists() and sha(ROOT/p)==h for p,h in preserved.items())
    assert sha(Path.home()/'.atari800.cfg')==pre['owner_config_sha256']
    result=dict(status='PASS',base_commit=pre['HEAD_before'],ATR_sha256=sha(BUILD/'candidate.atr'),
                campaign_sha256=pre['campaign_sha256'],campaign_id=disk['campaign_id'],all_60_board_sectors_identical=True,
                replay_60='PASS cold boot, real device playback, solved states, finale and Continue',
                FIX1='PASS 60 authored rectangles and padding composition',native_pixel_comparisons=pixels,
                levels=records,bank_free_minima=free,art_bytes_changed_by_area=areas,
                XEX_differences=diff,ATR_non_art_differences=outside,unchanged_runtime_sources=list(sources),
                runtime='Only fourteen palette-admission constants differ; instructions, symbols, stacks, undo and save ABI identical',
                memory=mem,additional_RAM_bytes=0,additional_code_bytes=0,additional_DLI_instructions=0,
                DLI_max_elapsed_clocks=timing['isr_max_clocks'][2],DLI_max_elapsed_PAL=timing['isr_max_clocks'][2]/35568,
                timing=timing,before_timing=old_timing,display_lists=dli,identical_config_inputs_states=True,
                all_run_observed=observed,RC1_save_tests=6,
                clean_rebuild_ATR_identical=True,preserved_files=len(preserved),owner_config_unchanged=True,
                reused_evidence=dict(checkpoint='f5df646',report='docs/art-final/REPORT.md',
                    native_undo256='ASan/UBSan + sim65 full60; nine witnesses over256; runtime and maps unchanged',
                    ENG4='Finite pin waveform RZRRZ; ISR/input/publication implementation unchanged',
                    saves='Cross-campaign identity and board-CRC rejection; additional RC1 tests separate',
                    audio='RECOVERY1 long audio, music assets and runtime byte-identical'),
                owner_acceptance=pre['owner_acceptance'],RC1_visual_owner='PENDING',RC1_hardware='NOT_RUN')
    dump(DOC/'verification.json',result);dump(DOC/'packed-levels.json',disk)
    print('PASS RC1: boards60, replay60, rasters120, FIX1, exact data-only scope, memory, DL/DLI, clean rebuild')

if __name__=='__main__':main()
