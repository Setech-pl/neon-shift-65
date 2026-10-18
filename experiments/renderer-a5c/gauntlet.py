#!/usr/bin/env python3
"""Candidate-only native headless evidence, deterministic hardware inputs."""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from emulator_smoke import run
from verify import labels,check
ROOT=Path(os.environ.get('NEON_A5C_BUILD','build/renderer-a5c'))
ROUTINES=['_display_counters','_game_step','_undo_pop','_display_changed','_display_animate','publish_update','_music_update','_load_package']
def probe(name,events,captures,total=850,variant='candidate',patch=True,boot=False,audio=False,trace_override=None):
    l=labels(ROOT/(variant+'.lbl'))
    os.environ['NEON_ATARI800']=os.environ.get('NEON_A5B_OBSERVER','/private/tmp/neon-a4-observer/src/atari800')
    os.environ['NSQ_ADDRS']=','.join(f'{l[n]:04x}' for n in ['_foreground_publication_end','publish_update','_publish_pending','_publish_count','_publish_addr_lo','_publish_addr_hi','_gs','_phase'])
    os.environ['NSQ_PHASE']=','.join(f'{l.get(n,0):04x}' for n in ['_display_animate','_phase_commit','_robot_update','_next_robot_base','_next_robot_push','_next_robot_ticks','_visible_robot_base','_visible_robot_push','_robot_animation','_robot_frame','_phase_generation','_video_clock','_publish_pending','_critical_guard','_robot_bank_a','_robot_bank_b','_next_robot_bank_a','_next_robot_bank_b','_ambient_active'])
    os.environ['NSQ_STATE']=','.join(f'{l[n]:04x}' for n in ['_asset_loading','_audio_calls','_input_head','_input_tail','order_index','music_row','music_tick'])
    trace=['_input_read','_display_counters','_render_number','_render_hud_text','_render_ratio','_display_changed','_display_animate','_hud_request','_hud_work','_hud_invalidate','_game_step','_undo_pop','_publish_now','_hud_commit','_hud_cancel','_asset_load_begin','_hud_adjust','hud_paint','_render_docks','_level_is_solved']
    if trace_override is not None:trace=trace_override
    os.environ['NSQ_TRACE']=','.join(f'{l.get(n,0):04x}' for n in trace)
    os.environ['NSQ_EPOCH']=f"{l.get('_hud_epoch',0):04x},{l['_hud_pending']:04x}"
    os.environ['NSQ_INPUT_CAPTURE']=f"{l.get('_poll_capture',0):04x},{l.get('input_sample',0):04x}"
    os.environ['NSQ_META']=','.join(f'{l.get(n,0):04x}' for n in ['_hud_ready_epoch','_hud_committed_epoch','_hud_state_moves','_hud_state_pushes','_hud_state_docks','_hud_dirty'])
    out=run(str(ROOT.relative_to('build'))+'/'+name,events,captures,total,xex=str(ROOT/(variant+'.xex')),
        labels_path=str(ROOT/(variant+'.lbl')),atr=str(ROOT/(variant+'.atr')),routines=ROUTINES,sio_patch=patch,boot=boot,audio=audio)
    (out/'trace-symbols.json').write_text(json.dumps(trace,indent=2)+'\n')
    # Cold boot / incomplete loading may intentionally have no active raster.
    if not boot:check(out,captures)
    return out
def main():
    name=sys.argv[1] if len(sys.argv)>1 else 'medium'
    events=[(300,300,dict(fire=0))];captures=[250,570]
    if name in ('medium','dim'):
        # Includes delivery to first dock (second L), then undo/re-delivery.
        for i,c in enumerate('RURURULL'):events.append((600+i*12,600+i*12,dict(stick={'R':7,'U':14,'L':11}[c])))
        events.extend([(710,710,dict(fire=0)),(722,722,dict(stick=11))])
        captures+=list(range(595,748))
    elif name in ('stress','carry','wrap'):
        for i,c in enumerate('URRDL'):events.append((600+i*10,600+i*10,dict(stick={'R':7,'U':14,'L':11,'D':13}[c])))
        for i in range(24):events.append((660+i*4,660+i*4,dict(fire=0) if i%2==0 else dict(stick=11)))
        captures+=list(range(595,770))
    elif name in ('burst','burst-dock'):
        if name=='burst-dock':
            for f,c in zip([600,610,620,630],'URRD'):events.append((f,f,dict(stick={'R':7,'U':14,'D':13}[c])))
        events.extend([(640,640,dict(stick=7 if name=='burst' else 11)),(641,641,dict(fire=0))])
        probe('final-'+name,events,list(range(595,657)),700,variant='carry');return
    elif name=='late-input':
        os.environ['NSQ_LATE_INPUT']='640,48,7,1'
        # Hold the injected pins across frame641's normal hardware refresh;
        # the actual press begins at640/line48, not the playback frame boundary.
        out=probe('final-late-input',[(300,300,dict(fire=0)),(641,641,dict(stick=7))],[250]+list(range(635,658)),700,variant='carry')
        (out/'pipeline.json').write_text(json.dumps(dict(scene=1,seed='3999999999',path='R',frames=[640],variant='carry',input_origin_csv='subframe-input.csv',hardware_subframe_fixture=[640,48,7,1]),indent=2)+'\n');return
    elif name=='small':
        events.extend([(550,550,dict(consol=6)),(570,570,dict(stick=11)),(590,590,dict(consol=3)),
            (900,900,dict(stick=11)),(914,914,dict(fire=0)),(930,930,dict(consol=3)),
            (1100,1100,dict(consol=6)),(1120,1120,dict(fire=0)),(1140,1140,dict(stick=11)),
            (1160,1160,dict(fire=0)),(1180,1180,dict(consol=6)),(1200,1200,dict(consol=6)),
            (1215,1215,dict(stick=11)),
            (1300,1300,dict(consol=6)),(1320,1320,dict(consol=5)),(1490,1490,dict(stick=13)),(1510,1510,dict(fire=0)),(1710,1710,dict(fire=0))])
        captures=[250,570,850]+list(range(895,935))+[1080,1110,1130,1150,1170,1190,1210,1310,1470,1500,1700,1730]+list(range(1214,1221))+list(range(1709,1715))
        probe('final-small',events,captures,1750);return
    elif name=='cold':
        probe('final-cold',[(2200,2200,dict(fire=0))],[400,800,2100,3000,3400],3800,patch=False,boot=True);return
    elif name=='song':
        probe('final-song',[(300,300,dict(fire=0))],list(range(230,271))+[570,2000,4000,6700],6800,audio=True);return
    elif name=='full':
        path=json.loads((ROOT/'solutions.json').read_text())[0]['path']
        inputs=[]
        for i,c in enumerate(path):
            f=600+i*12;events.append((f,f,dict(stick={'R':7,'U':14,'L':11,'D':13}[c])));inputs.append(f)
        end=inputs[-1]+30
        for i in range(len(path)):
            f=end+i*12;events.append((f,f,dict(fire=0)));inputs.append(f)
        captures=sorted(set([250,570]+[f+k for f in inputs for k in [-1,0,1,2,3]]))
        probe('final-full',events,captures,inputs[-1]+60);return
    elif name in ('continuous','continuous-dock','counter9','counter99','blocked','restart-pending','leave-pending','bank-burst','top-burst'):
        variant='carry';scene=1;seed='3999999999';path='RZ';fs=[640,641]
        if name=='continuous':path='RZUZ'*16;fs=list(range(640,704))
        elif name=='continuous-dock':path='URRD'+'LZUZ'*16;fs=[600,610,620,630]+list(range(640,704))
        elif name in ('counter9','counter99'):variant=name;seed='9' if name=='counter9' else '99'
        elif name=='blocked':path='R';fs=[640]
        elif name in ('restart-pending','leave-pending'):path='R';fs=[640]
        elif name=='top-burst':
            path='L'+'U'*4+'R'*15+'UUZ';fs=[600+i*12 for i in range(21)]+[900,901]
        elif name=='bank-burst':
            variant='candidate';scene=0;seed=None
            solution=json.loads((ROOT/'solutions.json').read_text())[0]['path'];path=solution+'Z'*len(solution)
            fs=list(range(600,648,2))+list(range(652,700,2))
        for f,c in zip(fs,path):events.append((f,f,dict(fire=0) if c=='Z' else dict(stick={'R':7,'U':14,'L':11,'D':13}[c])))
        if name=='blocked':events.append((641,641,dict(stick=13)))
        if name=='restart-pending':events.append((641,641,dict(consol=3)))
        # Pause cancels the outstanding HUD at641. Resident UI preparation
        # blanks DMA for642..644; SELECT647 follows the complete pause screen.
        if name=='leave-pending':events.extend([(641,641,dict(consol=6)),(647,647,dict(consol=5))])
        out=probe('final-'+name,events,[250]+list(range(595,940 if name=='top-burst' else 780))+[1000],1050,variant=variant)
        (out/'pipeline.json').write_text(json.dumps(dict(scene=scene,seed=seed,path=path,frames=fs,variant=variant,hardware_events=events),indent=2)+'\n');return
    else:raise ValueError(name)
    probe('final-'+name,events,captures,820,variant=name if name in ('stress','dim','carry','wrap') else 'candidate')
if __name__=='__main__':main()
