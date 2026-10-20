"""FINAL-FIX1: reveal the prepared display only inside the lower PAL border."""
from finish2_overlay import replace

def install(source):
    p=source/'display.c';s=p.read_text()
    old='static void activate(void){if(phase!=6)loading_finish();asset_loading=0;REG(0x230)=0x60;REG(0x231)=0x9f;REG(0x2f3)=2;REG(0xd401)=2;display_active=1;}'
    new='''static void activate(void){
    if(phase!=6)loading_finish();
    /* DMA is off throughout preparation. Publish both OS and hardware DL
       before VBI can enable DMA; never restart the loader with game PMG.
       The bounded border leaves time for neon_prepare before the next VBI. */
    while(REG(0xd40b)<124 || REG(0xd40b)>130){}
    REG(0x230)=REG(0xd402)=0x60;REG(0x231)=REG(0xd403)=0x9f;
    REG(0x2f3)=REG(0xd401)=2;
    asset_loading=0;display_active=1;
}'''
    assert old in s;s=s.replace(old,new);p.write_text(s)
    p=source/'main.c';s=p.read_text()
    # Load/validate next state without exposing it. Auto-save is part of the
    # same loader presentation. All other prepare callers still reveal once.
    s=s.replace('static unsigned char prepare(unsigned char n,unsigned char restore)', 'static unsigned char prepare(unsigned char n,unsigned char restore,unsigned char reveal)')
    s=s.replace('}else play();','}else if(reveal)play();')
    import re
    s=re.sub(r'prepare\((fresh|save_level\(\)|0|scene|failed_scene),(0|1|failed_restore)\)',r'prepare(\1,\2,1)',s)
    s=s.replace('prepare(scene+1,0)', 'prepare(scene+1,0,0)')
    s=s.replace('asset_load_end();show_play();}else{asset_load_end();phase=11;', 'asset_load_end();play();}else{asset_load_end();phase=11;')
    assert 'prepare(scene+1,0,0)' in s
    p.write_text(s)

    # VBI owns DMA activation. Enabling here starts ANTIC in the middle of
    # its current raster even when the newly written DL itself is correct.
    replace(source/'hardware.s',
            '    jsr neon_dma                   ; single-line player DMA + normal playfield\n    sta $022f\n    sta $d400\n    rts',
            '    ; First DMA is enabled by native_vbi on the next complete frame.\n    rts')
