"""Bounded RC2 presentation changes, applied only in an isolated build tree."""
import os

def replace(path,old,new):
    text=path.read_text();assert text.count(old)==1,(path,old)
    path.write_text(text.replace(old,new))

def install(source):
    d=source/'display.c'
    # Factor equal palette entries: same exact allowlist, room for presentation
    # initialization without enlarging any memory region or stack.
    replace(d,'pf1[4]={154,186,138,58},pf2[4]={2,2,2,2},pf0[4]={238,238,238,238},pf3[4]={6,6,6,6}',
              'pf1[4]={154,186,138,58}')
    for index,value in ((536,238),(538,2),(539,6)):
        name={536:'pf0',538:'pf2',539:'pf3'}[index]
        replace(d,f'DESC[{index}]=={name}[area-1]',f'DESC[{index}]=={value}')
    # ANTIC F title starts at104: cyan title, warm options, neutral footer.
    replace(d,'for(i=1;i<80;i++)DLIST[j++]=15;',
              'for(i=1;i<80;i++)DLIST[j++]=15|(i==79?128:0);')
    replace(d,'for(i=1;i<20;i++)DLIST[j++]=15;',
              'for(i=1;i<20;i++)DLIST[j++]=15|(i==19?128:0);')
    replace(d,'dli_font[0]=0x8c;dli_pf1[0]=0xd8;dli_pf2[0]=0;',
              'finish2_menu_palette();')
    replace(d,'#include <string.h>','#include <string.h>\nvoid finish2_menu_palette(void);')
    with (source/'hardware.s').open('a') as f:
        f.write('''
; Foreground only, show_menu has stopped DMA. No ISR or cc65 scratch.
.segment "CODE"
.export _finish2_menu_palette
_finish2_menu_palette:
    lda #$8c
    sta _dli_font
    sta _dli_font+1
    sta _dli_font+2
    lda #14
    sta _dli_pf1
    sta _dli_pf1+1
    lda #6
    sta _dli_pf1+2
    lda #$90
    sta _dli_pf2
    lda #$e0
    sta _dli_pf2+1
    lda #0
    sta _dli_pf2+2
    rts
''')
    # Existing loader list is shared by early boot and resident system/shift
    # loading. Early boot leaves DLI disabled until native hardware_init.
    p=source/'loading_art.py'
    replace(p,'[0x0c]*63+[0x70]*6','[0x0c]*62+[0x8c]+[0x70]*6')
    replace(p,'[0x0f]*7+[0x30','[0x0f]*6+[0x8f]+[0x30')
    l=source/'loading.s'
    replace(l,'.segment "CODE"','.import _dli_font,_dli_pf1,_dli_pf2,dli_row\n.segment "CODE"')
    replace(source/'hardware.s','dli_row: .res 1','.export dli_row\ndli_row: .res 1')
    replace(l,'@label_done:\n','''@label_done:
    ; Nested packages may already have a live loader. Change the complete
    ; tables and both DL pointers only in the lower PAL border; the short
    ; setup ends before the next visible raster even at frame wrap.
@palette_blank:
    lda $d40b
    cmp #124
    bcc @palette_blank
    lda #$e0
    sta _dli_font
    sta _dli_font+1
    lda #14
    sta _dli_pf1
    lda #6
    sta _dli_pf1+1
    lda #$90
    sta _dli_pf2
    lda #0
    sta _dli_pf2+1
''')
    replace(l,'    sta $230\n','    sta $230\n    sta $d402\n')
    replace(l,'    sta $231\n','    sta $231\n    sta $d403\n')
    replace(l,'    sta $d018\n','    sta $d018\n    sta dli_row\n')
    n=int(os.environ.get('NEON_FINISH2_START','0'))
    if n:
        assert n in (1,16,31,46)
        replace(source/'main.c','startup();clock=input_clock;',
                f'startup();if(phase!=6){{continue_saved({n-1});input_rearm();}}clock=input_clock;')
        # Only save record identity differs; catalog and level CRC use the real
        # untouched campaign_id. Each test image has its own save namespace.
        p=source/'campaign.c'
        replace(p,'sector_buffer+10,campaign_id,4','sector_buffer+10,save_id,4')
        replace(p,'save_record+10,campaign_id,4','save_record+10,save_id,4')
