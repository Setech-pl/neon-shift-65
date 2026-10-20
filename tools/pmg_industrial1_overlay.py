"""Industrial extension after PMG1, preserving the validated PMG/SIO lifecycle."""
def install(source,out):
    f=source/'link.cfg';s=f.read_text()
    s=s.replace('start=$A000,size=$0800,fill=yes','start=$A400,size=$0400,fill=yes')
    s=s.replace(' PMG:file="",define=yes,start=$A800,size=$0800;',
                ' BANK1:file="",define=yes,start=$A000,size=$0400;\n PMG:file="",define=yes,start=$A800,size=$0800;')
    s=s.replace(' PMG:load=PMG,type=bss;', ' BANK1:load=BANK1,type=bss;\n PMG:load=PMG,type=bss;');f.write_text(s)
    f=source/'regions.s';s=f.read_text().replace('.segment "PMG"\n.res $800', '.segment "BANK1"\n.res $400\n.segment "PMG"\n.res $800');f.write_text(s)
    f=source/'render.s';s=f.read_text()
    # Shared renderer uses the correct object codes on both halves of a cell
    # crossing a font boundary. Recover resident space from retired animation.
    s=s.replace('.segment "GAMECODE"\n_render_cell:', '.segment "CODE"\n_render_cell:')
    s=s.replace('        lda #0\n        sta strip_offset', '        lda industrial_strip_offsets,y\n        sta strip_offset')
    s+='\n.segment "RODATA"\nindustrial_strip_offsets:\n.repeat 24,I\n .if I<13\n  .byte 0\n .else\n  .byte 24\n .endif\n.endrepeat\n';f.write_text(s)
    f=source/'hardware.s';s=f.read_text()
    # No mutable game decoration: retire its code and all 291 bytes of cache.
    start=s.index('background_update:\n');end=s.index('@menu:\n',start)
    s=s[:start]+'background_update:\n'+s[end:]
    start=s.index('_animation_reset:\n');end=s.index('.segment "CODE"\n_music_update',start)
    s=s[:start]+'_animation_reset:\n    rts\n'+s[end:]
    for name,n in [('anim_ticks',32),('anim_phases',32),('anim_slot',1),('anim_count',1),('anim_cursor',1),('anim_ptr',2)]:
        s=s.replace(f'{name}:.res {n}\n','')
    # Preload CHBASE before WSYNC; store immediately on its release. This
    # avoids both the old font on the next first line and changing the font
    # during the previous line's rightmost glyph DMA.
    s=s.replace('    sta $D40A\n    lda _dli_font,x\n    sta $D409',
                '    lda _dli_font,x\n    sta $D40A\n    sta $D409')
    f.write_text(s)
    f=source/'display.c';s=f.read_text()
    s=s.replace('DESC[543]==3','DESC[543]==4')
    s=s.replace('pf1[4]={234,186,74,58}','pf1[4]={232,184,72,56}')
    s=s.replace('for(i=2;i<24;i++)DLIST[j++]=4;', 'for(i=2;i<24;i++)DLIST[j++]=4|(i==12?128:0);')
    s=s.replace('dli_font[i]=0x8c','dli_font[i]=i<2?0x8c:0xa0')
    f.write_text(s)
    f=source/'validate.c';s=f.read_text()
    s=s.replace('bx!=20-DESC[541] || by!=13-DESC[542]', 'bx!=4 || by!=5')
    for line in ['    for(i=8;i<128;i++)if((DESC[i]&127)>=124)return 0;\n',
                 '    for(n=0;n<800;n++)if((COMPOSITION[n]&127)>=124)return 0;\n',
                 '    for(n=0;n<880;n++)if((BASE[n]&127)>=124)return 0;\n']:
        assert line in s;s=s.replace(line,'')
    f.write_text(s)
    f=source/'loader.c';s=f.read_text()
    s=s.replace('addresses[6]={0x8c00,0xa000,0x9800,0x1400,0xb160,0x9de0}', 'addresses[7]={0x8c00,0xa000,0xa400,0x9800,0x1400,0xb160,0x9de0}')
    s=s.replace('lengths[6]={1024,2048,880,800,640,544}', 'lengths[7]={1024,1024,1024,880,800,640,544}')
    s=s.replace('kind<4?3:2','kind<4?4:2').replace('sections=kind<4?6:', 'sections=kind<4?7:')
    f.write_text(s)
