#!/usr/bin/env python3
"""Limited VIS1 evidence checks; never upgrades the historical ENGINE FAIL.

Independent XSB history and immutable ATR packages are compared with read-only
RAM, fetched raster codes and actual native RGB/HUD. This is a finite smoke,
not an ENG3 qualification matrix or a listening/hardware/owner review.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / 'build/vis1-energy-industrial-restore/r2'
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'experiments/eng3-observed-input-3pal'))
sys.path.insert(0, str(ROOT / 'experiments/art3-contextual-decoration-review'))
from capture import labels, state
from floor_restore import packages
from observed_oracle import Game, board_matches
from m1_check import png
PAL = 35568


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def csvrows(p):
    return [{k: int(v) for k, v in row.items()} for row in csv.DictReader(p.open())]


def equal_file(a, b):
    assert a.read_bytes() == b.read_bytes(), (a, b, 'changed bytes')
    return sha(a)


def hud_matches(path, expected, font, docks=0, total=4):
    im, pal = png(path)
    def region(x, y, width, text, start, bg, fg):
        wanted = [[False] * width for _ in range(8)]
        for i, c in enumerate(text):
            glyph = 38 if c == '/' else int(c) + 27
            for yy, value in enumerate(font[glyph*8:glyph*8+8]):
                for xx in range(6):
                    if value & (128 >> xx):
                        wanted[yy][start + i*7 + xx] = True
        return all(pal[im[y+yy][x+xx]] == pal[fg if wanted[yy][xx] else bg]
                   for yy in range(8) for xx in range(width))
    return (region(56, 32, 72, str(expected['moves']).zfill(2), 1, 0, 14)
        and region(200, 32, 72, str(expected['pushes']).zfill(2), 0, 0, 14)
        and region(288, 24, 40, f'{docks:02}/{total:02}', 1, 0xe0, 0xee))


def main():
    candidate = BUILD / 'area-1'
    baseline = BUILD / 'baseline/area-1'
    l = labels(candidate / 'candidate.lbl')
    b = labels(baseline / 'candidate.lbl')
    assert l == b, 'Linked layout changed'
    old = (baseline / 'candidate.xex').read_bytes()
    new = (candidate / 'candidate.xex').read_bytes()
    changes = [dict(offset=i, baseline=a, candidate=z)
               for i, (a, z) in enumerate(zip(old, new)) if a != z]
    assert len(old) == len(new) and changes == [], 'VIS1 executable changed'
    linked_diff = None
    unchanged = {name:equal_file(candidate/name, baseline/name)
                 for name in ('menu.nrq','music.nrq','splash.nrq','boot.bin',
                              'early-code.bin','early-splash.bin','early-packed.bin',
                              'early-text.bin','levels.json','solutions.json')}
    cross_area = {}
    for area in (2, 3, 4):
        a = BUILD / f'area-{area}'
        z = ROOT / f'build/visual-baseline/area-{area}'
        cross_area[str(area)] = {name:equal_file(a/name, z/name) for name in
            ('candidate.xex','candidate.atr','scene-0.nrq','scene-1.nrq','scene-2.nrq',
             'menu.nrq','music.nrq','splash.nrq')}
    source = (ROOT / 'experiments/eng3-observed-input-3pal/reference/prototype_assets.c').read_text()
    font = bytes(map(int, re.findall(r'\d+', re.search(
        r'const unsigned char mono_font\[\] = \{(.*?)\};', source, re.S)[1])))
    rows = json.loads((candidate/'levels.json').read_text())['levels'][0]['rows']
    solution = json.loads((candidate/'solutions.json').read_text())[0]['path']
    assert len(solution) == 69 and solution[:14] == 'RLDRDDLLURURUR'
    contents = packages((candidate/'candidate.atr').read_bytes())
    base_contents = packages((baseline/'candidate.atr').read_bytes())
    for s, bs in zip(contents[:3], base_contents[:3]):
        assert s[0xb160] == bs[0xb160], 'Robot frames changed'
        # Empty dock quarters may be allocated to different glyph indices.
        for bank, address in enumerate((0x8c00,0xa000,0xa400,0xa800,0xac00)):
            for q in range(4):
                code=s[0x9de0][8+bank*24+8+q]&127
                old_code=bs[0x9de0][8+bank*24+8+q]&127
                assert s[address][code*8:code*8+8]==bs[address][old_code*8:old_code*8+8]
    model = Game(rows)
    expected = {950:model.state()}
    for i, c in enumerate(solution, 1):
        assert model.request(c)['accepted']
        if i == 14:
            expected[1220] = model.state()
    expected[2120] = model.state()
    assert model.moves == 69 and model.pushes == 11
    states = {}
    for variant, labs, sections in [('baseline',b,base_contents), ('candidate',l,contents)]:
        out = BUILD/'captures'/f'{variant}-review'
        assert json.loads((out/'artifact.json').read_text())['ATR']['sha256'] == sha(
            (baseline if variant == 'baseline' else candidate)/'candidate.atr'), 'Capture ATR binding'
        data = json.loads((out/'states.json').read_text())
        initial_ram=(out/'frame-0950.ram').read_bytes()
        assert int.from_bytes(initial_ram[labs['_capacity']:labs['_capacity']+2],'little')==256
        for f, exp in expected.items():
            assert all(data[str(f)][k] == v for k, v in exp.items()), (variant,f,'history')
            assert board_matches((out/f'raster-{f:04}.ram').read_bytes(), exp, rows, sections[0])
            docks = {950:0,1220:1,2120:4}[f]
            assert data[str(f)]['docked'] == docks
            assert hud_matches(out/f'native-{f:04}.png', exp, font, docks), (variant,f,'native HUD')
        assert (data['3340']['scene'],data['3340']['docked']) == (1,9)
        assert (data['3780']['scene'],data['3780']['moves'],data['3780']['pushes']) == (2,0,0)
        assert (data['3860']['moves'],data['3860']['pushes'],data['3860']['docked']) == (1,1,1)
        assert not any(v['error'] or v['loading'] for f,v in data.items() if int(f)>=950)
        states[variant] = {str(f):data[str(f)] for f in [950,1220,2120,3340,3780,3860]}
    assert states['baseline'] == states['candidate']
    names = ('01-start-16x8','02-docked-16x8','03-replay69','04-max-20x10','05-small-6x3')
    archived_baseline = {name:equal_file(BUILD/f'captures/baseline-review/native-{f:04}.png',
        ROOT/f'docs/checkpoints/vis1-energy-industrial-restore/native/candidate/{name}.png')
        for name,f in zip(names,(950,1220,2120,3340,3780))}
    equal_file(BUILD/'captures/baseline-review/emulator.cfg',
               BUILD/'captures/candidate-review/emulator.cfg')
    ui = {}
    for f in (200,450,570,780,2180,2220):
        ui[str(f)] = equal_file(BUILD/f'captures/baseline-review/native-{f:04}.png',
                               BUILD/f'captures/candidate-review/native-{f:04}.png')
    assert sha(baseline/'candidate.atr') == 'e04e6adbfbd46254bf4125f0cbf649091618d24bafe335b95f9adaacdf7fcb5d'
    response = {}
    for variant, labs, sections in [('baseline',b,base_contents), ('candidate',l,contents)]:
        out = BUILD/'captures'/f'{variant}-response'
        assert json.loads((out/'artifact.json').read_text())['ATR']['sha256'] == sha(
            (baseline if variant == 'baseline' else candidate)/'candidate.atr'), 'Response ATR binding'
        clocks = {v['frame']:v['clock'] for v in csvrows(out/'input-clock.csv')}
        m = Game(rows)
        samples = []
        for f, action in [(1000,'R'),(1040,'Z'),(1080,'U')]:
            previous = m.state()
            request = m.request(action)
            exp = request['state']
            future = range(f, min(f+21,1091))
            for end in (future[-1],):
                actual = state((out/f'frame-{end:04}.ram').read_bytes(),labs)
                assert all(actual[k]==v for k,v in exp.items())
                ram=(out/f'frame-{end:04}.ram').read_bytes()
                assert int.from_bytes(ram[labs['_count']:labs['_count']+2],'little')==request['undo']
            matches = [v for v in future if board_matches(
                (out/f'raster-{v:04}.ram').read_bytes(), exp, rows, sections[0])]
            hud = [v for v in future if hud_matches(out/f'native-{v:04}.png',exp,font)]
            assert matches and hud
            if request['accepted']:
                first = matches[0]
                im, pal = png(out/f'native-{first:04}.png')
                before, bp = png(out/f'native-{f-1:04}.png')
                x,y=exp['player'];xx=8+(4+2*x)*8;yy=24+(5+2*y)*8
                assert any(pal[im[py][px]] != bp[before[py][px]]
                           for py in range(yy,yy+16) for px in range(xx,xx+16))
                bound_y=max(exp['player'][1],previous['player'][1])
                upper=(clocks[first]+(24+(5+2*bound_y)*8+16+8)*114-clocks[f]+8)/PAL
                hud_upper=(clocks[hud[0]]+48*114-clocks[f]+8)/PAL
                assert upper<=3 and hud_upper<=3, (variant,action,upper,hud_upper)
            else:
                assert exp == previous and not request['accepted']
                upper=hud_upper=0
            samples.append(dict(action=action,input_frame=f,accepted=request['accepted'],
                undo=request['undo'],state=exp,visible_frame=matches[0],hud_frame=hud[0],
                complete_board_upper_PAL=upper,complete_HUD_upper_PAL=hud_upper))
        response[variant]=samples
    phase = {}
    music = {}
    for variant, labs, sections in [('baseline',b,base_contents), ('candidate',l,contents)]:
        out=BUILD/'captures'/f'{variant}-review'
        desc=sections[0][0x9de0]
        count=desc[4]
        periods=[desc[128+i*8+2] for i in range(count)]
        initial=[desc[128+i*8+3] for i in range(count)]
        previous=None;transitions=[0]*count
        for f in range(950,991):
            ram=(out/f'frame-{f:04}.ram').read_bytes()
            ticks=list(ram[labs['anim_ticks']:labs['anim_ticks']+count])
            phases=list(ram[labs['anim_phases']:labs['anim_phases']+count])
            if previous:
                pt,pp=previous
                for i,period in enumerate(periods):
                    assert ticks[i]==(pt[i]+1)%period, (variant,f,i,'timer')
                    want=(pp[i]+(32 if ticks[i]==0 else 0))&96
                    assert phases[i]==want, (variant,f,i,'independent phase')
                    transitions[i]+=int(ticks[i]==0)
            previous=ticks,phases
        assert all(transitions)
        phase[variant]=dict(descriptors=count,periods=periods,initial_phases=initial,
                           transitions=transitions,checked_intervals=40,status='PASS')
        schedule=csvrows(out/'frame-schedule.csv')
        pairs=[(p,q) for p,q in zip(schedule,schedule[1:]) if 950<=p['frame']<2120]
        bad=[p['frame'] for p,q in pairs if (q['audio_calls']-p['audio_calls'])%256!=1
             or q['skctl']!=3 or q['audctl']!=0 or p['loading'] or q['loading']]
        assert not bad, (variant,'music schedule',bad)
        music[variant]=dict(status='PASS',active_pairs=len(pairs),bad=bad,
            orders=sorted({p['order'] for p,q in pairs}),method='One music call per active PAL frame; POKEY device registers. Not listening.')
    assert phase['baseline']['periods']==phase['candidate']['periods']
    assert phase['baseline']['initial_phases']==phase['candidate']['initial_phases']
    timing=json.loads((BUILD/'captures/candidate-review/timing.json').read_text())
    assert timing['csp_outside_samples']==0
    memory=dict(MAIN_free=32768-l['__BSS_RUN__']-l['__BSS_SIZE__'],
        LOW_free=5120-l['__LOADBSS_RUN__']-l['__LOADBSS_SIZE__'],
        ZP_free=256-l['__ZP_LAST__'],C_stack_reserved=2048,HW_stack_reserved=256,
        undo_bytes=l['_count']-l['_history'],undo_capacity=256,
        C_stack_observed_peak=timing['c_stack_sample_peak'],
        HW_stack_observed_peak=timing['hardware_stack_observed_peak'],
        csp_outside_samples=timing['csp_outside_samples'],
        stack_note='Finite read-only samples; full ENG3 reservations retained',
        glyph_banks={str(s):[v['free'] for v in json.loads(
            (candidate/f'scene-{s}-banks.json').read_text())['banks']] for s in range(3)})
    assert memory['undo_bytes']==256 and min(memory[k] for k in ('MAIN_free','LOW_free','ZP_free'))>0
    result=dict(status='PASS limited VIS1 checks',engine_status='ENGINE FAIL (historical; not requalified)',
        contract='ENG3-B-v1',owner_visual='OWNER NOT_RUN',
        ATR_sha256=sha(candidate/'candidate.atr'),baseline_ATR_sha256=sha(baseline/'candidate.atr'),
        executable_diff=changes,linked_difference_address=linked_diff,
        executable_diff_reason='No linked executable bytes or addresses changed versus VIS1 9dab436',
        unchanged_packages=unchanged,areas_2_4=cross_area,review_states=states,
        identical_UI_native=ui,identical_VIS1_archived_native=archived_baseline,
        response=response,phase=phase,music=music,memory=memory,
        limitations=['No full ENG3 matrix','No owner visual run','No listening','No hardware/SIO2SD run'])
    (BUILD/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],response=response,memory=memory),indent=2))


def _block_offsets(data):
    """XEX file offsets -> linked address, excluding its segment headers."""
    i=0
    while i<len(data):
        if data[i:i+2]==b'\xff\xff':
            i+=2
            continue
        start,end=struct.unpack_from('<HH',data,i);i+=4
        n=end-start+1
        yield i,start,n
        i+=n


if __name__=='__main__':
    main()
