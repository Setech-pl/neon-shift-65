"""HWVIS1: static SIO-safe loader, dark UI; gameplay banks/input ISR preserved."""
from finish2_overlay import replace

def install(source):
    # ANTIC C illustration uses PF0; ANTIC F label/bar use PF1/PF2.
    # A single fixed palette needs no phase reset by deferred OS VBI during SIO.
    replace(source/'loading_art.py','[0x0c]*62+[0x8c]+[0x70]*6','[0x0c]*63+[0x70]*6')
    replace(source/'loading_art.py','[0x0f]*6+[0x8f]+[0x30','[0x0f]*7+[0x30')
    p=source/'loading.s';s=p.read_text()
    a=s.index('    lda #$e0\n    sta _dli_font');b=s.index('    lda #$00\n    sta $230',a)
    s=s[:a]+s[b:]
    # Complete hardware and OS shadows before publishing this screen.
    s=s.replace('    sta $2c4\n','    sta $2c4\n    sta $d016\n').replace('    sta $2c5\n','    sta $2c5\n    sta $d017\n').replace('    sta $2c6\n    sta $2c8\n    jmp loading_text','''    sta $2c6
    sta $d018
    sta $2c8
    sta $d01a
    sta dli_row
    jsr loading_text
    lda #1
    sta _asset_loading
    lda #$22
    sta $22f
    sta $d400
    rts''')
    s=s.replace('.import _dli_font,_dli_pf1,_dli_pf2,dli_row','.import _asset_loading,dli_row')
    p.write_text(s)
    # No VBI may expose the old game list as a loader while setup is incomplete.
    replace(source/'sio.s','    lda #1\n    sta _asset_loading\n    lda #0','    lda #0')
    # Both bootstrap and resident loader publish exact matching shadows/registers.
    p=source/'early-support.s';s=p.read_text()
    for shadow,hw in (('$230','$d402'),('$231','$d403'),('$2f4','$d409'),('$2c4','$d016'),('$2c5','$d017'),('$2c6','$d018'),('$2c8','$d01a')):
        s=s.replace('    sta '+shadow+'\n','    sta '+shadow+'\n    sta '+hw+'\n')
    p.write_text(s)
    # FINISH2's blue title/loader, warm options and first HUD row were deliberate.
    # Keep foreground contrast/selection arrow, use black text background.
    replace(source/'hardware.s','    lda #$90\n    sta _dli_pf2\n    lda #$e0\n    sta _dli_pf2+1\n    lda #0\n    sta _dli_pf2+2','    lda #0\n    sta _dli_pf2\n    sta _dli_pf2+1\n    sta _dli_pf2+2')
    replace(source/'display.c','colors(0x90,14,DESC[6]==1?0xe0:(DESC[536]&0xf0));','colors(0x90,14,0);')
    # Before the first enabled DLI, phase and tables must be initialized. The
    # boot loader now has no DLI, so init has no dependency on unfilled tables.
    replace(source/'hardware.s','    sta _asset_loading\n    sta _infra_enabled','    sta _asset_loading\n    sta dli_row\n    sta _infra_enabled')
