"""Reproducible PMG1 source transform, after HWVIS1. No generated-tree edits."""
from pathlib import Path
from hwvis1_overlay import replace
ROOT=Path(__file__).resolve().parents[1]

def install(source,out):
    cfg=source/'link.cfg';s=cfg.read_text()
    begin=s.index(' BANK1:file=');end=s.index(' ROBOTSOURCE:',begin)
    s=s[:begin]+f' OVERLAY:file="{out / "renderer.bin"}",define=yes,start=$A000,size=$0800,fill=yes;\n PMG:file="",define=yes,start=$A800,size=$0800;\n'+s[end:]
    s=s.replace('start=$B160,size=$0500','start=$B160,size=$0280')
    begin=s.index(' BANK1:load=');end=s.index(' ROBOTSOURCE:load=',begin)
    s=s[:begin]+' GAMECODE:load=OVERLAY,type=ro,define=yes;\n GAMERODATA:load=OVERLAY,type=ro,define=yes;\n PMG:load=PMG,type=bss;\n'+s[end:];cfg.write_text(s)
    f=source/'regions.s';s=f.read_text();begin=s.index('.segment "BANK1"');end=s.index('.segment "ROBOTSOURCE"',begin)
    s=s[:begin]+'.segment "PMG"\n.res $800\n'+s[end:];f.write_text(s.replace('.res $500','.res $280'))
    # Game-only functions/tables use overlay. Text/HUD stays resident.
    f=source/'render.s';s=f.read_text()
    s=s.replace('.segment "CODE"\n_render_cell:', '.segment "GAMECODE"\n_render_cell:')
    begin=s.index('    ldy #2\n',s.index('_render_cell:'));end=s.index('@boxes:',begin)
    s=s[:begin]+s[end:]
    s=s.replace('    lda strip_offsets,y\n','    lda #0\n')
    a=s.index('object:\n');b=s.index('static:\n',a)
    s=s[:a]+'object:\n'+s[b:]
    a=s.index('strip_offsets:\n');b=s.index('.segment \"CODE\"',a)
    s=s[:a]+s[b:]
    # Cell renderer data/tables are small; shared resident math tables retained.
    s=s.replace('.segment "CODE"\n_display_changed:', '.segment "GAMECODE"\n_display_changed:')
    begin=s.index('@player:\n',s.index('_display_changed:'));end=s.index('@boxes:\n',begin)
    s=s[:begin]+'@player:\n'+s[end:]
    begin=s.index('    lda _old_boxes,y\n',s.index('@boxes:\n',s.index('_display_changed:')));end=s.index('@old:\n',begin)
    s=s[:begin]+s[end:]
    begin=s.index('    lda _gs+764,y\n',s.index('@new:\n',s.index('_display_changed:')));end=s.index('@draw_new:\n',begin)
    s=s[:begin]+s[end:]
    begin=s.index('.segment "CODE"\n_display_animate:');end=s.index('; Bounded decimal cache',begin)
    s=s[:begin]+(ROOT/'src/pmg1/animate.s').read_text()+'\n'+s[end:]
    f.write_text(s)
    (source/'phase.s').write_text((ROOT/'src/pmg1/phase.s').read_text())
    f=source/'hardware.s';s=f.read_text()
    # Resident gates: no IRQ can enter an overwritten overlay in menu/SIO/UI.
    s=s.replace('    jsr _phase_tick              ; tick the PREVIOUS visible action once', '''    lda _pmg_active
    beq :+
    jsr _phase_tick
:''')
    s=s.replace('    lda #$22\n    bne @display_set','    lda _pmg_active\n    beq :+\n    lda #$3a\n    bne @display_set\n:   lda #$22\n    bne @display_set')
    s=s.replace('    lda _publish_count\n    beq :+\n    lda #1\n    sta _critical_guard\n:', '    lda #1\n    sta _critical_guard')
    s=s.replace('_publish_now:\n', '_publish_now:\n    lda _display_active\n    beq @safe\n')
    # Native PMG publication only in whole-board blank. Remove row shortcut.
    begin=s.index('    ; Earliest changed screen row');end=s.index('@safe:',begin)
    s=s[:begin]+'    jmp _foreground_publication_end\n'+s[end:]
    begin=s.index('_robot_update = robot_update');end=s.index('_background_update =',begin)
    s=s[:begin]+'.import _robot_update\n'+s[end:]
    s=s.replace('.export _robot_frame,_robot_update','.export _robot_frame')
    s+='\n'+(ROOT/'src/pmg1/resident.s').read_text();f.write_text(s)
    # Descriptor bounds are validated against actual immutable board padding.
    f=source/'validate.c';s=f.read_text()
    s=s.replace('bx!=20-w || by!=13-h || count>32', 'DESC[541]<1 || DESC[541]>16 || DESC[542]<1 || DESC[542]>8 || bx!=20-DESC[541] || by!=13-DESC[542] || count!=0')
    s=s.replace('    return 1;','''    for(j=0;j<8;j++)for(k=0;k<16;k++)
        if((k>=DESC[541] || j>=DESC[542]) && ((GameState *)0xb680)->map[j][k]!='#')return 0;
    return 1;''');f.write_text(s)
    f=source/'display.c';s=f.read_text()
    s=s.replace('!DESC[541] && !DESC[542] && !DESC[543]', 'DESC[543]==3')
    s=s.replace('void video_off(void){','void pmg_off(void);\nvoid pmg_prepare(void);\nvoid pmg_on(void);\nvoid video_off(void){')
    s=s.replace('asset_loading=0;display_active=ambient_active=menu_active=0;', 'pmg_off();asset_loading=0;display_active=ambient_active=menu_active=0;')
    s=s.replace('for(i=2;i<24;i++)DLIST[j++]=4|((i==5 || i==9 || i==13 || i==17)?128:0);','for(i=2;i<24;i++)DLIST[j++]=4;')
    s=s.replace('dli_font[i]=banks[i-1]','dli_font[i]=0x8c')
    s=s.replace('    video_off();hud_enabled=1;', '    video_off();if(loaded!=1)return;pmg_prepare();hud_enabled=1;')
    s=s.replace('++render_full_boards;activate();','++render_full_boards;activate();pmg_on();')
    s=s.replace('REG(0x26f)=0;display_active=1;', 'display_active=1;')
    # Full logical padding may extend beyond physical screen when centered.
    s=s.replace('unsigned char i,x,y,j=0;', 'unsigned char i,x,y,vw,vh,j=0;')
    s=s.replace('render_board_x=DESC[2];render_board_y=DESC[3];', 'render_board_x=DESC[2];render_board_y=DESC[3];vw=DESC[541];vh=DESC[542];')
    s=s.replace('for(y=0;y<gs.height;y++)for(x=0;x<gs.width;x++)', 'for(y=0;y<vh;y++)for(x=0;x<vw;x++)')
    s=s.replace('static const unsigned char banks[5]={0x8c,0xa0,0xa4,0xa8,0xac};','')
    f.write_text(s)
    # Disable PMG before loader can overwrite any game resources, including
    # menus. The original begin already drains publication via video_off().
    f=source/'sio.s';s=f.read_text().replace('.import _hud_cancel','.import _video_off').replace(':   jsr _hud_cancel',':   jsr _video_off');f.write_text(s)
    f=source/'loader.c';s=f.read_text()
    s=s.replace('addresses[9]={0x8c00,0xa000,0xa400,0xa800,0xac00,0x9800,0x1400,0xb160,0x9de0}', 'addresses[6]={0x8c00,0xa000,0x9800,0x1400,0xb160,0x9de0}')
    s=s.replace('lengths[9]={1024,1024,1024,1024,1024,880,800,1280,544}', 'lengths[6]={1024,2048,880,800,640,544}')
    s=s.replace('HEADER[4]!=2','HEADER[4]!=(kind<4?3:2)').replace('sections=kind<4?9:', 'sections=kind<4?6:')
    f.write_text(s)
    # Repack AFTER the final link, binding the exact overlay bytes and CRCs.
    f=source/'build.py';s=f.read_text()
    begin=s.index("for name,define in [");end=s.index(']:',begin)
    s=s[:begin]+"for name,define in [('candidate',None)"+s[end:]
    f.write_text(s)
