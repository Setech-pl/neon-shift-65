"""Options UI uses the same 2 KB window as LEVELSELECT1, never another bank."""
from pathlib import Path
import subprocess,struct,re
ROOT=Path(__file__).resolve().parents[1]
def replace(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def install(source,out):
    p=source/'main.c';s=p.read_text()
    s=replace(s,'void selector_open(void);','void selector_open(void);\nvoid options_open(void);')
    s=replace(s,'static unsigned char resume(void)','unsigned char resume(void)')
    s=replace(s,'else if(selected==3){previous_phase=0;phase=7;show_ui();}','else if(selected==3){previous_phase=0;options_open();}')
    old='else if(action==INPUT_OPTION){if(!prepare(scene,0,1)){phase=6;show_ui();}}'
    assert s.count(old)==2
    s=s.replace(old,'else if(action==INPUT_OPTION){previous_phase=phase;options_open();}',1)
    s=replace(s,'else if(action==INPUT_FIRE){previous_phase=3;phase=7;show_ui();}','else if(action==INPUT_FIRE){previous_phase=3;options_open();}')
    a=s.index('        }else if(phase==7){');b=s.index('        }else if(phase==11){',a)
    s=s[:a]+s[b:]
    s=replace(s,'else if(failed_kind==6)selector_open();','else if(failed_kind==6)selector_open();\n                else if(failed_kind==7)options_open();')
    p.write_text(s)
    p=source/'display.c';s=p.read_text();a=s.index('    else if(phase==7){');b=s.index('\n    else if(phase==9)',a);s=s[:a]+s[b:]
    s=s.replace('START PAUSE / OPTION RESTART','START PAUSE / OPTION OPTIONS')
    p.write_text(s)
    p=source/'loading.s';s=p.read_text()
    s='.import _menu_transition\n'+s
    for label in ('_loading_begin:','_loading_label:'):
        s=replace(s,label,label+'\n    ldx _menu_transition\n    beq :+\n    rts\n:')
    p.write_text(s)
    # Owner follow-up: STEPS at the right edge; its digits remain aligned
    # there as the count grows. Move PUSHES to the vacated left field.
    p=source/'display.c';s=p.read_text()
    s=replace(s,'hud_text(0,1,"STEPS:",7);hud_text(136,1,"PUSHES:",7);','hud_text(201,1,"STEPS:",7);hud_text(0,1,"PUSHES:",7);')
    p.write_text(s)
    p=source/'render.s';s=p.read_text()
    s=replace(s,'''    txa
    clc
    adc hud_first_move
    tay
    cpy #10
    bcs @blank
    lda _hud_move_digits,y''','''    txa
    cmp hud_first_move
    bcc @blank
    tay
    lda _hud_move_digits,y''')
    xs=[250+7*i for i in range(10)]+[56+7*i for i in range(10)]+[281,288,295,302,309]
    addresses=[0x9400+(x//8)*8 if i<20 else 0x9540+(x//8)*8-232 for i,x in enumerate(xs)]
    tables=dict(hud_positions_lo=[a&255 for a in addresses],hud_positions_hi=[a>>8 for a in addresses],
                hud_masks_low=[255^(252>>(x%8)) for x in xs],hud_masks_high=[255^((252<<(8-x%8))&255) for x in xs],
                hud_shifts=[10*(x%8) for x in xs])
    for name,values in tables.items():
        s,n=re.subn(r'^'+name+r':\.byte .*$',name+':.byte '+','.join(map(str,values)),s,flags=re.M);assert n==1
    for suffix,op in [('lo','<'),('hi','>')]:
        a=s.index('hud_slash_'+suffix+':');b=a
        for _ in range(26):b=s.index('\n',b)+1
        s=s[:a]+'hud_slash_'+suffix+':\n'+'\n'.join(' .byte '+op+'(hud_slash+'+str(x%8)+'*16)' for x in xs)+'\n'+s[b:]
    p.write_text(s)
    p=source/'hardware.s';s=p.read_text()
    s=replace(s,'    sta _selector_seen','    sta _selector_seen\n    sta _menu_transition')
    s=replace(s,'lda $9430+I\n        sta $9170+I','lda $94f8+I\n        sta $9238+I')
    s=replace(s,'lda $94c0+I\n        sta $9200+I','lda $9438+I\n        sta $9178+I')
    p.write_text(s)
    p=source/'build.py';s=replace(p.read_text(),'        link_overlay(OUT,SOURCE)','        link_overlay(OUT,SOURCE)\n        from menufix1 import link_overlay as link_options\n        link_options(OUT,SOURCE)');p.write_text(s)
def link_overlay(out,source):
    (out/'options-entry.s').write_text('.segment "ENTRY"\n.import _options_run\njmp _options_run\n')
    subprocess.run(['ca65','-o',str(out/'options-entry.o'),str(out/'options-entry.s')],check=True)
    subprocess.run(['cl65','-t','atari','-Oirs','-Cl','-g','-I'+str(out),'-I'+str(source),'-I'+str(ROOT/'src'),'-c','-o',str(out/'options.o'),str(ROOT/'src/menufix1/options.c')],check=True)
    subprocess.run(['cl65','-t','atari','-C',str(out/'selector.cfg'),'-m',str(out/'options.map'),'-Ln',str(out/'options.lbl'),'-o',str(out/'options.bin'),str(out/'options-entry.o'),str(out/'options.o'),str(out/'selector-resident.o')],check=True)
def pack(image,out):
    from warehouses import crc16
    from atr import offset
    raw=(out/'options.bin').read_bytes();assert len(raw)==2048
    at=offset(657,128);assert not any(image[at:at+2176]),'Options sector collision'
    header=bytearray(128);header[:8]=b'NSLS'+bytes((1,0xa0,0,8));struct.pack_into('<H',header,8,crc16(raw))
    image[at:at+2176]=header+raw
