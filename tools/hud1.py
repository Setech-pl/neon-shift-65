"""HUD1: colour only the first existing ANTIC 2 row, using its DLI boundary."""
def install(source):
    path = source / 'display.c'
    text = path.read_text()
    marker = '    colors(0x90,14,0);\n    dli_font[0]=0x90;'
    assert text.count(marker) == 1
    # ANTIC 2 takes foreground hue from COLPF2 and luminance from COLPF1.
    # PF2 luminance stays zero. DLI slot 0 restores neutral row 2; slot 1
    # already restores the exact game font/PF1/PF2 before ANTIC 4 begins.
    text = text.replace(marker, '    colors(0x90,14,DESC[536]&0xf0);\n    dli_font[0]=0x90;')
    path.write_text(text)
