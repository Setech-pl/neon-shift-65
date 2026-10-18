#!/usr/bin/env python3
"""Audit final disk geometry, pixel rasters, runtime scope and DLI prototype."""
import csv
import hashlib
import json
import re
import statistics
from pathlib import Path
from recovery1_audit import extract,sector
from product1_gauntlet import setup
from product1_fix1_review import BANKS,sections,live,animations
import verify

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/art-final'
DOC=ROOT/'docs/art-final'
PAL=35568


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def memory(build):
    labs=verify.labels(build/'candidate.lbl');segments=[]
    for n,start,end,size,align in re.findall(r'^([A-Z_0-9]+)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{5})$',(build/'candidate.map').read_text(),re.M):
        if n in ('EXEHDR','MAINHDR','LOADHDR','COMHDR','EXTRAHDR','AUTOSTRT'):continue
        start,size,align=int(start,16),int(size,16),int(align,16)
        segments.append(dict(name=n,start=start,end=start+size,bytes=size,alignment=align))
    for i,s in enumerate(segments):
        assert s['start']%s['alignment']==0
        for t in segments[i+1:]:assert s['end']<=t['start'] or t['end']<=s['start']
    used=lambda start,end:max(s['end'] for s in segments if start<=s['start']<end)-start
    named=lambda name:next(s['bytes'] for s in segments if s['name']==name)
    result=dict(MAIN_free=0x6000-used(0x2000,0x8000),LOW_free=0xe00-used(0x600,0x1400),
                ZP_free=0x100-max(s['end'] for s in segments if s['name']=='ZEROPAGE'),
                PERSIST_free=512-named('PERSIST'),music_tail_free=496-named('EXTRA'),
                CODE_bytes=named('CODE'),BSS_bytes=named('BSS'),C_stack_reserved=named('CSTACK'),hardware_stack_reserved=256,
                undo_depth=256,segments=segments)
    assert labs['__STACKSIZE__']==result['C_stack_reserved']==2048
    assert all(result[k]>=0 for k in ('MAIN_free','LOW_free','ZP_free','PERSIST_free','music_tail_free'))
    return result


def dl_info(ram,labs):
    at=0x9f60;start=at;y=0;items=[];interrupts=[]
    while True:
        op=ram[at];at+=1;mode=op&15
        if mode==1:at+=2;break
        h=((op>>4)&7)+1 if mode==0 else 8
        address=None
        if mode and op&64:address=int.from_bytes(ram[at:at+2],'little');at+=2
        items.append(dict(y=y,height=h,mode=mode,opcode=op,LMS=address))
        if op&128:interrupts.append(y+h-1)
        y+=h
    return dict(address=start,bytes=at-start,raw=list(ram[start:at]),end_scanline=y,
                DLI_last_scanlines=interrupts,table_font=list(ram[labs['_dli_font']:labs['_dli_font']+6]),
                table_PF1=list(ram[labs['_dli_pf1']:labs['_dli_pf1']+6]),
                table_PF2=list(ram[labs['_dli_pf2']:labs['_dli_pf2']+6]),instructions=items)


def wall_tiles(sec,level,devices):
    occupied={(x,y) for d in devices for y in range(d['y'],d['y']+d['height']) for x in range(d['x'],d['x']+d['width'])}
    w,h=level['visual_size'];rows=level['rows'];result={5:set(),10:set()}
    for y in range(h):
        for x in range(w):
            if rows[y][x]!='#' or (x,y) in occupied:continue
            mask=sum(bit for dx,dy,bit in ((0,-1,1),(1,0,2),(0,1,4),(-1,0,8)) if 0<=x+dx<w and 0<=y+dy<h and rows[y+dy][x+dx]=='#')
            if mask not in result:continue
            tile=bytearray()
            for q in range(4):
                code=sec[0x1400][(y*20+x)*4+q];row=5+y*2+q//2;bank=BANKS[min((row-2)//4,4)]
                tile.extend(bytes([code&128])+sec[bank][(code&127)*8:(code&127)*8+8])
            result[mask].add(bytes(tile))
    return result


def main():
    build=BASE/'final';before=ROOT/'build/recovery1/owner-vis1r2';prototype=BASE/'bands-prototype'
    source=ROOT/'assets/levels/camp2-b/campaign.json';raw=source.read_bytes();levels=json.loads(raw)['levels']
    pre=json.loads((DOC/'preflight.json').read_text());assert sha(source)==pre['campaign_sha256']
    image=(build/'candidate.atr').read_bytes();old=(before/'candidate.atr').read_bytes();disk=extract(build/'candidate.atr')
    assert len(disk['levels'])==60 and disk['campaign_id']==hashlib.sha256(raw).hexdigest()[:8]
    runtime=json.loads((build/'campaign-full/campaign-result.json').read_text());assert runtime['status']=='PASS' and len(runtime['levels'])==60
    labs=setup(build);pixels=0;bank_free=[124]*5;records=[];unique_before={5:set(),10:set()};unique_after={5:set(),10:set()}
    for n,(level,packed,run) in enumerate(zip(levels,disk['levels'],runtime['levels'])):
        assert packed['rows']==level['rows'] and packed['number']==level['number'] and packed['area']==level['area'] and packed['name']==level['name']
        assert sector(image,1100+n*70)==sector(old,1100+n*70)
        sec=sections(image,n);prior=sections(old,n)
        if n>=15:assert sector(image,1101+n*70,69)==sector(old,1101+n*70,69)
        assert [a[:3] for a in animations(sec)]==[a[:3] for a in animations(prior)]
        w,h=level['visual_size'];pad=0
        for y in range(8):
            for x in range(16):
                if x<w and y<h:continue
                assert level['rows'][y][x]=='#';pad+=1
                for q in range(4):
                    pos=(5+y*2+q//2)*40+4+x*2+q%2
                    assert sec[0x1400][(y*20+x)*4+q]==sec[0x9800][pos-80]
        banks=json.loads((build/f"art-area-{level['area']}/level-{n+1:02d}/scene-0-banks.json").read_text())
        for i,b in enumerate(banks['banks']):
            assert b['used']<=128 and b['dynamic_reserved']==4 and not b['conflicts']
            bank_free[i]=min(bank_free[i],b['free'])
        if n<15:
            a=wall_tiles(sec,level,banks['devices']);b=wall_tiles(prior,level,banks['devices'])
            for mask in (5,10):unique_after[mask]|=a[mask];unique_before[mask]|=b[mask]
        initial=run['frame']-run['moves']*8-15
        for f in (initial,run['frame']):pixels+=live(build/'campaign-full',f,labs,sec)['pixels']
        records.append(dict(number=n+1,area=level['area'],size=[w,h],free_cells=packed['free_cells'],boxes=len(packed['boxes']),goals=len(packed['goals']),padding_cells=pad,board_crc16=packed['board_crc16'],status='PASS'))
    x=(before/'candidate.xex').read_bytes();y=(build/'candidate.xex').read_bytes()
    diff=[dict(offset=i,before=a,after=b) for i,(a,b) in enumerate(zip(x,y)) if a!=b]
    assert len(x)==len(y) and diff==[dict(offset=19884,before=34,after=2)]
    outside=[];art_changed=0
    for i,(a,b) in enumerate(zip(old,image)):
        if a==b:continue
        sec=(i-16)//128+1
        if 1101<=sec<=2149 and (sec-1100)%70:art_changed+=1
        else:outside.append(dict(offset=i,before=a,after=b))
    assert len(old)==len(image) and outside==[dict(offset=24415,before=34,after=2)]
    for name in ('hardware.s','input.c','main.c','campaign.c','link.cfg','regions.s','move.s','undo-fast.s','phase.s','render.s'):
        assert (before/'source'/name).read_bytes()==(build/'source'/name).read_bytes(),name
    assert (before/'candidate.lbl').read_bytes()==(build/'candidate.lbl').read_bytes()
    mem={v:memory(p) for v,p in (('before',before),('final',build),('bands',prototype))}
    captures={v:json.loads((BASE/('captures-'+v+'.json')).read_text()) for v in ('before','final','bands')}
    dli=[];helper=[]
    for index,number in enumerate((1,5,9)):
        reference=captures['before'][index]
        for v in ('final','bands'):
            r=captures[v][index]
            assert r['input_sha256']==reference['input_sha256'] and r['config_sha256']==reference['config_sha256']
            for frame in r['states']:
                assert all(r['states'][frame][k]==reference['states'][frame][k] for k in ('scene','phase','player','boxes','moves','pushes','undo'))
        row={}
        for v in ('final','bands'):
            r=captures[v][index];out=ROOT/r['out'];l=verify.labels(out/'candidate.lbl');ram=(out/f"raster-{r['initial']:04}.ram").read_bytes()
            dl=dl_info(ram,l);assert dl['bytes']==32 and dl['DLI_last_scanlines']==[31,39,71,103,135,167]
            expect=[14,156,154,156,154,156] if v=='bands' else [14,156,156,156,156,156]
            assert dl['table_PF1']==expect and dl['table_PF2']==[0,2,2,2,2,2]
            values=[int(t['cpu']) for t in csv.DictReader((out/'cpu-exclusive.csv').open()) if int(t['index'])==10 and r['initial']<=int(t['frame'])<=r['initial']+4]
            timing=json.loads((out/'timing.json').read_text())
            row[v]=dict(display_list=dl,DLI_idle_CPU_clocks=dict(samples=len(values),minimum=min(values),maximum=max(values),mean=statistics.mean(values)),
                        DLI_max_elapsed_clocks=timing['isr_max_clocks'][2],DLI_max_elapsed_PAL=timing['isr_max_clocks'][2]/PAL)
            if v=='bands':helper.extend(int(t['clocks']) for t in csv.DictReader((out/'routines.csv').open()) if t['index']=='7')
        assert row['final']['display_list']['raw']==row['bands']['display_list']['raw']
        dli.append(dict(level=number,measurements=row))
    def handler(p):
        s=(p/'source/hardware.s').read_text();return s[s.index('native_dli:\n'):s.index('; Only ISR owns queue producer')]
    assert handler(before)==handler(build)==handler(prototype)
    eng4=json.loads((build/'eng4-art-final/eng4-result.json').read_text())
    assert eng4['exactly_one_ordered_full_image_per_accepted_action']
    assert [a['action'] for a in eng4['accepted_actions']]==list('RZRRZ')
    assert eng4['accepted_actions'][-2]['state']['pushes']==2 and eng4['accepted_actions'][-1]['state']['pushes']==1
    assert eng4['maxima']['external_to_accept_pal']<=6 and eng4['maxima']['accept_to_full_pal']<=4 and eng4['maxima']['external_to_full_pal']<=10
    timings=[json.loads(p.read_text()) for p in build.glob('*/timing.json')];assert all(t['csp_outside_samples']==0 for t in timings)
    mem['final']['observed_C_stack_peak']=max(t['c_stack_sample_peak'] for t in timings)
    mem['final']['observed_HW_stack_peak']=max(t['hardware_stack_observed_peak'] for t in timings)
    native=json.loads((build/'native-campaign/result.json').read_text());assert native['status']=='PASS'
    saves=json.loads((BASE/'save-results.json').read_text());assert saves['status']=='PASS'
    (DOC/'packed-levels.json').write_text(json.dumps(disk,indent=2)+'\n')
    result=dict(status='PASS',ATR_sha256=sha(build/'candidate.atr'),campaign_path=str(source.relative_to(ROOT)),campaign_sha256=sha(source),
                new_60_boards_identical_to_verified_recovery_snapshot=True,areas_2_4_packages_identical=True,all_symbols_identical=True,
                XEX_differences=diff,runtime_note='One palette-admission data byte; no final runtime instruction changes',
                ATR_non_art_differences=outside,Energy_art_bytes_changed=art_changed,menu_splash_boot_music_save_slots_identical=True,
                FIX1_padding='PASS all60 authored rectangles',native_pixel_comparisons=pixels,levels=records,
                bank_free_minima=bank_free,wall_tile_variation={str(m):dict(before=len(unique_before[m]),after=len(unique_after[m])) for m in (5,10)},
                memory=mem,native_replay=native,save_tests=len(saves['tests']),ENG4=dict(status='PASS finite waveform',maxima=eng4['maxima'],accepted_actions=len(eng4['accepted_actions'])),
                DLI_prototype=dict(included=False,reason='Shared PF1 bands cut through robot and devices; uniform metal retained for readability',
                                   additional_BSS_bytes=0,additional_code_bytes=mem['bands']['CODE_bytes']-mem['final']['CODE_bytes'],
                                   linked_MAIN_consumption=mem['final']['MAIN_free']-mem['bands']['MAIN_free'],
                                   additional_DLI_instructions=0,nominal_additional_clocks_per_active_frame=0,
                                   helper_observed_elapsed_clocks=[min(helper),max(helper)],caller_JSR_clocks=6,
                                   helper_with_caller_observed_PAL=[(min(helper)+6)/PAL,(max(helper)+6)/PAL],measurements=dli),
                reused_checks='RECOVERY1 long audio/music and untouched ENG4/undo/save implementation; exact source/asset binding checked here',
                visual_owner='NOT_RUN',hardware='NOT_RUN')
    (DOC/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS disk60, replay60, FIX1, native rasters, scopes, memory, DLI prototype, save isolation, ENG4; memory',mem['final']['MAIN_free'],mem['final']['LOW_free'],mem['final']['ZP_free'],flush=True)


if __name__=='__main__':main()
