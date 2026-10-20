#!/usr/bin/env python3
"""Extend the frozen VIS1-r2 engine in an isolated PRODUCT1 output."""
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/eng3-observed-input-3pal'
PRODUCT=ROOT/'experiments/product1'

def hardware(source):
    s=(source/'hardware.s').read_text()
    # Keep compatibility addresses/labels, release the old 384-byte raw FIFO.
    s=s.replace('_queued_stick: .res 128\n_queued_trigger: .res 128\n_queued_console: .res 128',
                '_queued_stick: .res 1\n_queued_trigger: .res 1\n_queued_console: .res 1\n'
                '.export _eng4_edges,_eng4_buttons\n_eng4_edges: .res 1\n_eng4_buttons: .res 1\neng4_temp: .res 1\neng4_lock: .res 1')
    start=s.index('input_sample:\n');end=s.index('; Main publishes the mask',start)
    s=s[:start]+'''input_sample:
    inc _input_clock
    lda eng4_lock
    bne eng4_sample_done
eng4_capture:
    lda $d300
    and #15
    sta _poll_stick
    lda $d010
    and #1
    sta _poll_trigger
    eor #1
    sta eng4_temp
    lda $d01f
    and #7
    sta _poll_console
    eor #7
    and #6
    ora eng4_temp
    sta eng4_temp
    lda _poll_console
    eor #7
    and #1
    asl a
    asl a
    asl a
    ora eng4_temp
    sta eng4_temp
    eor _eng4_buttons
    and eng4_temp
    tax
    and #1
    beq eng4_latch
    lda _eng4_busy
    beq eng4_latch
    ; FIRE observed while an action finishes is an undo intention, including
    ; the winning push. Advancing needs a fresh FIRE after publication settles.
    txa
    and #254
    ora #2
    tax
eng4_latch:
    txa
    ora _eng4_edges
    sta _eng4_edges
    lda eng4_temp
    sta _eng4_buttons
eng4_sample_done:
    rts
''' + s[end:]
    start=s.index('_input_probe:\n');end=s.index('.export _splash_clock_sync',start)
    s=s[:start]+'''_input_probe:
_poll_capture:
    lda #1
    sta eng4_lock
    jsr eng4_capture
    lda #0
    sta eng4_lock
    ldx #0
    rts
.export _eng4_take_edges
_eng4_take_edges:
    lda #1
    sta eng4_lock
    ; One bit per control. Clear the highest priority bit only; other
    ; simultaneous controls survive until a phase transition/rearm.
    lda _eng4_edges
    and #3
    beq eng4_console
    tax
    lda _eng4_edges
    and #252
    sta _eng4_edges
    txa
    and #2
    bne eng4_release
    lda #1
    bne eng4_release
eng4_console:
    lda _eng4_edges
    and #8
    bne eng4_take
    lda _eng4_edges
    and #4
    bne eng4_take
    lda #0
eng4_take:
    tax
    eor _eng4_edges
    sta _eng4_edges
    txa
eng4_release:
    tax
    lda #0
    sta eng4_lock
    txa
    ldx #0
    rts
''' + s[end:]
    start=s.index('_input_wait:\n')
    s=s[:start]+'''_input_wait:
    sta wait_clock
eng4_wait:
    jsr _input_probe
    lda _input_clock
    cmp wait_clock
    bne eng4_wake
    lda _eng4_busy
    bne eng4_wait
    lda _eng4_edges
    bne eng4_wake
    lda _poll_stick
    cmp _poll_last_stick
    bne eng4_wake
    jmp eng4_wait
eng4_wake:
    rts
.import _eng4_busy
'''
    (source/'hardware.s').write_text(s)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--area',type=int,default=1);p.add_argument('--campaign',action='store_true');p.add_argument('--visual2',action='store_true',help='Offline Energy artwork/palette overlay; requires --campaign')
    p.add_argument('--art4',choices=('A','B'),help='Energy-only ART4-A asset direction, same campaign engine')
    p.add_argument('--art-final',action='store_true',help='Energy ART-FINAL on recovered VIS1-r2 assets')
    p.add_argument('--finish1',action='store_true',help='v1.0-RC1 common industrial artwork for all four areas; requires --art-final')
    p.add_argument('--band-colors',action='store_true',help='ART-FINAL: use existing DLI palette slots for alternating metal shades')
    a=p.parse_args();os.chdir(ROOT);out=ROOT/a.out
    if a.art_final and (not a.campaign or a.art4 or a.visual2):p.error('--art-final requires --campaign and excludes --visual2/--art4')
    if a.band_colors and not a.art_final:p.error('--band-colors requires --art-final')
    if a.finish1 and (not a.art_final or a.band_colors):p.error('--finish1 requires --art-final and excludes diagnostic bands')
    if a.art4:
        if not a.campaign:p.error('--art4 requires --campaign')
        a.visual2=True
    if a.visual2 and not a.campaign:p.error('--visual2 requires --campaign')
    if out.exists():raise SystemExit('Refusing existing output: '+str(out))
    source=out/'source';shutil.copytree(BASE,source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    vis=ROOT/'experiments/vis1-energy-industrial-restore'
    shutil.copyfile(vis/'r2/energy.py',source/'vis1_energy.py');shutil.copyfile(vis/'energy.py',source/'vis1_base.py')
    c=source/'compile.py';s=c.read_text().replace("if __name__=='__main__':main()", "import vis1_energy\nvis1_energy.install(sys.modules[__name__])\nif __name__=='__main__':main()")
    c.write_text(s)
    if a.campaign:
        # PRODUCT1-FIX1: only offline composition changes. Preserve the 16x8
        # collision/save ABI, absolute board origin and existing device plan.
        s=c.read_text()
        s=s.replace("rows=level['rows'];w=len(rows[0]);h=len(rows);bx=20-w;by=13-h",
                    "rows=level['rows'];w=len(rows[0]);h=len(rows);bx=20-w;by=13-h\n    vw,vh=level.get('visual_size',(w,h))")
        s=s.replace('if bx<=col<bx+2*w and by<=row<by+2*h:continue',
                    'if bx<=col<bx+2*vw and by<=row<by+2*vh:continue')
        s=s.replace("elif rows[y][x]=='#':", "elif x>=vw or y>=vh:\n            data=decorative.get((x,y))\n        elif rows[y][x]=='#':")
        s=s.replace("c=b.intern(data[q*8:q*8+8],f'cell{x},{y}/q{q}')",
                    "c=screen[pos-80] if data is None else b.intern(data[q*8:q*8+8],f'cell{x},{y}/q{q}')")
        if a.visual2 or a.art_final:
            s=s.replace("if 0<=x+dx<w and 0<=y+dy<h and rows[y+dy][x+dx]=='#')",
                        "if 0<=x+dx<(vw if themes.AREA==1 else w) and 0<=y+dy<(vh if themes.AREA==1 else h) and rows[y+dy][x+dx]=='#')")
        c.write_text(s)
    hardware(source)
    if a.band_colors:
        # No new DLI or per-frame work: write two already-resident palette
        # slots only while show_play has DMA stopped. ENG4 ISR stays intact.
        f=source/'hardware.s'
        f.write_text(f.read_text()+'''\n.segment "CODE"
.export _art_final_bands
_art_final_bands:
    lda $9de6
    cmp #1
    bne @done
    lda #$9a
    sta _dli_pf1+2
    sta _dli_pf1+4
@done:rts
''')
    shutil.copyfile(PRODUCT/'input.c',source/'input.c')
    (source/'input_atari.c').write_text('/* ENG4 acquisition and admission share input.c. */\n')
    h=source/'candidate.h';h.write_text(h.read_text()+'\nunsigned char eng4_take_edges(void);\nvoid eng4_accepted(void);\n')
    m=source/'main.c';s=m.read_text().replace('if(moved)display_changed(pushed);','if(moved){eng4_accepted();display_changed(pushed);}')
    m.write_text(s)
    if a.campaign:
        cfg=source/'link.cfg';s=cfg.read_text().replace(' TRAILER:file=%O', ' PERSIST:file="",define=yes,start=$9600,size=$0200;\n EXTRAHDR:file=%O,start=0,size=4;\n SPARERAM:file=%O,start=$1E10,size=$01F0;\n TRAILER:file=%O').replace(' AUTOSTRT:load=TRAILER',' PERSIST:load=PERSIST,type=bss;\n EXTRAHDR:load=EXTRAHDR,type=ro;\n EXTRA:load=SPARERAM,type=ro,define=yes;\n AUTOSTRT:load=TRAILER').replace('MUSICRAM:file="",define=yes,start=$1800,size=$0800','MUSICRAM:file="",define=yes,start=$1800,size=$0610');cfg.write_text(s)
        regions=source/'regions.s';regions.write_text(regions.read_text().replace('.segment "MUSICRAM"\n.res $800','.segment "MUSICRAM"\n.res $610'))
        header=source/'header.s';header.write_text(header.read_text()+'\n.import __EXTRA_LOAD__,__EXTRA_SIZE__\n.segment "EXTRAHDR"\n.word __EXTRA_LOAD__,__EXTRA_LOAD__+__EXTRA_SIZE__-1\n')
        for name in ('main.c','campaign.c','campaign.h'):shutil.copyfile(PRODUCT/name,source/name)
        if os.environ.get('NEON_CAMPAIGN'):
            from product1_data import load
            _,levels=load();count=len(levels)
            # Build configuration of the same campaign loop and validator.
            # No movement, input, undo, rendering or save-format changes.
            path=source/'campaign.c';s=path.read_text()
            s=s.replace('>=60',f'>={count}').replace('!=60',f'!={count}').replace('!=59',f'!={count-1}')
            if any(l['area']!=i//15+1 for i,l in enumerate(levels)):
                s=s.replace('sector_buffer[6]!=n/15+1','sector_buffer[6]!=campaign_areas[n]')
                s='static const unsigned char campaign_areas[]={'+','.join(str(l['area']) for l in levels)+'};\n'+s
            path.write_text(s)
            path=source/'main.c';path.write_text(path.read_text().replace('scene==59',f'scene=={count-1}'))
        s=(source/'loader.c').read_text().replace('#include "candidate.h"','#include "campaign.h"')
        s=s.replace('static unsigned char catalog[128],catalog_ready,reading_catalog;','#pragma bss-name(push,"PERSIST")\nstatic unsigned char catalog[128];\n#pragma bss-name(pop)\nstatic unsigned char catalog_ready,reading_catalog;')
        s=s.replace('if(start<5 || total<144', 'if(kind==1)start=1101+(unsigned int)level_number*70;\n    if(start<5 || total<144')
        (source/'loader.c').write_text(s)
        sio=source/'sio.s';s=sio.read_text().replace('    lda #$52\n    sta $0302\n    lda #$40', '''    ldy #$52
    jmp sio_command
.export _sio_write
_sio_write:
    sta $030A
    stx $030B
    lda #$31
    sta $0300
    lda #1
    sta $0301
    ldy #$57
sio_command:
    sty $0302
    lda #$40
    cpy #$52
    beq :+
    lda #$80
:''')
        sio.write_text(s)
        d=source/'display.c';s=d.read_text().replace('#include "candidate.h"','#include "campaign.h"')
        s=s.replace('static const unsigned char pf1[4]={156,188,76,56},pf2[4]={34,178,66,50};','static const unsigned char pf1[4]={156,188,76,56},pf2[4]={34,178,66,50},pf0[4]={238,190,78,60},pf3[4]={230,186,74,58};')
        if a.visual2:s=s.replace('pf1[4]={156,188,76,56},pf2[4]={34,178,66,50}', 'pf1[4]={154,188,76,56},pf2[4]={148,178,66,50}')
        if a.art_final:s=s.replace('pf2[4]={34,178,66,50}', 'pf2[4]={2,178,66,50}')
        if a.finish1:
            s=s.replace('pf1[4]={156,188,76,56},pf2[4]={2,178,66,50},pf0[4]={238,190,78,60},pf3[4]={230,186,74,58}',
                        'pf1[4]={154,186,138,58},pf2[4]={2,2,2,2},pf0[4]={238,238,238,238},pf3[4]={6,6,6,6}')
        if a.band_colors:
            s='void art_final_bands(void);\n'+s
            marker='for(i=1;i<6;i++){dli_font[i]=banks[i-1];dli_pf1[i]=DESC[537];dli_pf2[i]=DESC[538];}'
            assert s.count(marker)==1
            s=s.replace(marker,marker+'\n    art_final_bands();')
        if a.art4:
            pf1,pf2=(8,4) if a.art4=='A' else (152,148)
            s=s.replace('pf1[4]={154,188,76,56},pf2[4]={148,178,66,50}',f'pf1[4]={{{pf1},188,76,56}},pf2[4]={{{pf2},178,66,50}}')
            if a.art4=='B':s=s.replace('pf0[4]={238,190,78,60}','pf0[4]={14,190,78,60}')
        s=s.replace('DESC[536]==AREA_PF0','DESC[536]==pf0[area-1]').replace('DESC[539]==AREA_PF3','DESC[539]==pf3[area-1]')
        s=s.replace('colors(0x90,14,AREA_HUD);','colors(0x90,14,DESC[6]==1?0xe0:(DESC[536]&0xf0));')
        s=s.replace('prototype_levels[scene].name','level_name').replace('"TOP SCORES"','"HOW TO PLAY"')
        s=s.replace('if(phase==6){', 'if(phase==10){text(7,10,"SHIFT COMPLETE 60/60");text(11,7,"ALL FOUR AREAS RESTORED");if(save_error)text(13,3,"SAVE FAILED: SELECT RETRY");text(15,7,"FIRE RETURN TO TITLE");}\n    else if(phase==11){text(7,5,"PROGRESS SAVE FAILED");text(11,5,"SELECT RETRY / FIRE CONTINUE");}\n    else if(phase==8){if(save_error==3)text(7,7,"SAVE DISK READ FAILED");else if(save_error==2)text(7,7,"CORRUPT OR INCOMPATIBLE SAVE");else text(7,7,"NO SAVED SHIFT");text(11,7,"BEGIN SHIFT STARTS LEVEL 1");text(15,7,"FIRE RETURN TO TITLE");}\n    else if(phase==6){')
        s=s.replace('text(12,9,"QUALIFICATION ONLY");text(16,9,"START RETURN TO TITLE");','text(5,3,"STICK MOVE / FIRE OR SELECT UNDO");text(8,3,"START PAUSE / OPTION RESTART");text(11,3,"SOLVED: FIRE NEXT / SELECT UNDO");text(14,3,"PAUSED: SELECT SAVE AND EXIT");text(17,3,"UNDO IS EMPTY AFTER COLD RESUME");text(20,3,"START OR FIRE RETURN TO TITLE");')
        s=s.replace('text(10,8,"LEFT / RIGHT SCENE");','text(10,8,"SELECT SAVE AND EXIT");')
        s=s.replace('text(14,8,"SELECT RETURN TO TITLE");','if(save_error==4)text(14,4,"SAVE FAILED: SELECT RETRY / START PLAY");else text(14,8,"SAVES USE THIS WRITABLE DISK");')
        s=s.replace('text(6,16,"CONFIG");','text(6,16,"CONFIG");text(8,9,music_enabled?"MUSIC ON":"MUSIC OFF");text(14,9,sfx_enabled?"SFX ON":"SFX OFF");')
        if os.environ.get('NEON_CAMPAIGN') and count!=60:
            s=s.replace('SHIFT COMPLETE 60/60',f'CAMP2 COMPLETE {count:02d}/{count:02d}').replace('ALL FOUR AREAS RESTORED','SIX CAMPAIGN SAMPLES' if count==6 else 'CAMPAIGN SAMPLES')
        d.write_text(s)
        v=source/'validate.c';s=v.read_text().replace('w!=strlen(prototype_levels[kind-1].rows[0]) || h!=prototype_levels[kind-1].height','w!=16 || h!=8')
        s=s.replace("prototype_levels[kind-1].rows[(n-by)/2][(k-bx)/2]!='#'", "((GameState *)0xb680)->map[(n-by)/2][(k-bx)/2]!='#'")
        v.write_text(s)
        b=source/'build.py';s=b.read_text().replace("cmd(sys.executable,SOURCE/'compile.py')", "cmd(sys.executable,SOURCE/'compile.py')\n    from product1_runtime import prepare\n    prepare(OUT,SOURCE)")
        s=s.replace("files=[SOURCE/'display.c'", "files=[SOURCE/'campaign.c',SOURCE/'display.c'")
        s=s.replace("begin=parser.index('unsigned char level_try_move('","parser=parser.replace('unsigned char level_load(GameState *gs, const Level *lvl)', '#if !defined(__ATARI__)\\nunsigned char level_load(GameState *gs, const Level *lvl)')\n    parser=parser.replace('signed char level_box_at(', '#else\\nunsigned char level_load(GameState *gs,const Level *lvl){return 0;}\\n#endif\\nsigned char level_box_at(')\n    begin=parser.index('unsigned char level_try_move('")
        s=s.replace("common=[OUT/'replay.c',OUT/'assets.c'", "common=[OUT/'replay.c',OUT/'fixture-assets.c'")
        s=s.replace("(OUT/'level.c').write_text(parser)","begin=parser.index('#else\\nunsigned char level_load');end=parser.index('#endif',begin)\n    parser=parser[:begin]+'#endif'+parser[end+6:]\n    begin=parser.index('signed char level_box_at(');end=parser.index('#if !defined(__ATARI__) && !defined(NATIVE_MOVE)',begin)\n    parser=parser[:begin]+'#ifndef __ATARI__\\n'+parser[begin:end]+'#endif\\n'+parser[end:]\n    (OUT/'level.c').write_text(parser)")
        s=s.replace("files=[SOURCE/'campaign.c'", "game=Path('src/game.c').read_text().replace('unsigned char game_start(', '#ifndef __ATARI__\\nunsigned char game_start(').replace('unsigned char game_step(', '#endif\\nunsigned char game_step(')\n    (OUT/'game.c').write_text(game)\n    files=[SOURCE/'campaign.c'")
        s=s.replace("OUT/'assets.c',Path('src/game.c')", "OUT/'assets.c',OUT/'game.c'")
        s=s.replace("path=OUT/(name+'.atr');path.write_bytes(image)","from product1_runtime import pack\n    pack(image,OUT)\n    path=OUT/(name+'.atr');path.write_bytes(image)")
        b.write_text(s)
        shutil.copyfile(ROOT/'tools/product1_runtime.py',source/'product1_runtime.py')
    if os.environ.get('NEON_FINISH2')=='1':
        assert a.finish1
        from finish2_overlay import install
        install(source)
    if os.environ.get('NEON_RELEASE1')=='1':
        d=source/'display.c';s=d.read_text()
        assert 'pf1[4]={154,186,138,58}' in s
        d.write_text(s.replace('pf1[4]={154,186,138,58}','pf1[4]={234,186,74,58}'))
    if os.environ.get('NEON_HWVIS1')=='1':
        from hwvis1_overlay import install
        install(source)
    if os.environ.get('NEON_PMG1')=='1':
        assert os.environ.get('NEON_HWVIS1')=='1'
        from pmg1_overlay import install
        install(source,out)
    if os.environ.get('NEON_PMG_INDUSTRIAL1')=='1':
        from pmg_industrial1_overlay import install
        install(source,out)
    if os.environ.get('NEON_ENERGY_DETAIL1')=='1':
        from energy_detail1_overlay import install
        install(source)
    if os.environ.get('NEON_ENERGY_FINAL1')=='1':
        f=source/'display.c'
        s=f.read_text()
        assert 'DESC[536]==(area==1?40:238)' in s
        f.write_text(s.replace('DESC[536]==(area==1?40:238)','DESC[536]==238'))
    if os.environ.get('NEON_ENERGY_FIX1')=='1':
        from energy_fix1_ambient import install
        install(source)
    if os.environ.get('NEON_ENERGY_NEON1')=='1':
        from energy_neon1 import install
        install(source)
    if os.environ.get('NEON_AREAS1')=='1':
        from neon_areas1_art import install_runtime
        install_runtime(source)
    if os.environ.get('NEON_FINAL_FIX1')=='1':
        from final_fix1_overlay import install
        install(source)
    env=dict(os.environ,NEON_ART2_BUILD=str(out),NEON_ART2_AREA=str(a.area),NEON_ART2_FIXTURE='obstacles',ART3_VARIANT='B',NEON_VISUAL2=str(int(a.visual2)))
    env['NEON_ART_FINAL']=str(int(a.art_final))
    env['NEON_FINISH1']=str(int(a.finish1))
    if a.art4:env['NEON_ART4']=a.art4
    with (out/'build.log').open('w') as log:
        subprocess.run([sys.executable,str(source/'build.py')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    (out/'binding.json').write_text(json.dumps(dict(base='f8c6977',area=a.area,files={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in PRODUCT.glob('*') if f.is_file()},ATR_sha256=hashlib.sha256((out/'candidate.atr').read_bytes()).hexdigest()),indent=2)+'\n')
    print(out)
if __name__=='__main__':main()
