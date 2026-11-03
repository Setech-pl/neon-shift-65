"""ATMOSPHERE1: existing two-font screen-code animation, no extra PMG/DLI."""
import re
from neon_areas1_art import descriptors as existing_descriptors

LIGHTS={1:0x9c,2:0xbc,3:0x4c,4:0x3c}
# All four positions are outside even the maximum 16x8 puzzle rectangle.
EXTRA=((3,6,23),(3,24,41),(14,2,29),(22,29,61))

def artwork(background):
    previous=background.image
    def image(level):
        p=previous(level);c=background.c
        L=lambda x,y,xx,yy,v:c.line(p,x,y,xx,yy,v)
        R=lambda x,y,w,h,v:c.rect(p,x,y,w,h,v)
        # Recessed supply rail: three separately fed luminous lengths.
        for x,w in ((20,28),(82,24),(120,20)):
            L(x,26,x+w-1,26,1)
            R(x,27,2,1,3);R(x+w-2,27,2,1,3)
        # Existing lamp/glass, cabinet door and lower manifold remain intact.
        L(4,38,9,38,1)
        L(10,96,10,108,1);L(10,110,10,116,1)
        L(98,183,118,183,1);L(122,183,134,183,1)
        # Energy service markings retain the existing yellow crate ink PF1.
        if c.themes.AREA==1:
            R(5,36,4,2,2);R(67,26,3,2,2)
        vw,vh=level['visual_size'];right=16+vw*8
        if right<=120:
            x=right+8;w=152-x
            L(x+8,81,x+8,96,1)
            L(x+w-7,133,x+w-7,145,1)
            for xx in range(x+4,x+w-8,8):R(xx,154,3,2,1)
            if c.themes.AREA==2:
                for xx in range(x+4,x+w-7,7):L(xx+2,115,xx+2,119,1)
            elif c.themes.AREA==3:
                for yy in (109,115,121):L(x+5,yy,x+w-9,yy,1)
        else:
            # Fixed narrow riser leaves the full-size map at exactly (4,5).
            L(153,51,153,69,1);L(153,112,153,140,1)
        background.p=p
        return p
    background.image=image

def descriptors(background,level,fonts,screen):
    raw,meta=existing_descriptors(background,level,fonts,screen)
    p=background.image(level)
    for slot,(row,col,period) in enumerate(EXTRA,4):
        bank=int(row>=13);selector=background.selector(level,row,col)
        codes=[]
        for phase in range(4):
            q=[r[:] for r in p]
            # A small dim travelling gap, not an on/off flash of the fixture.
            if phase:
                x=col*4+(phase-1)%4
                for y in range(row*8,(row+1)*8):
                    if q[y][x]==1:q[y][x]=3
            glyph=background.glyph(q,row*40+col)
            if phase==0:
                code=screen[(row-2)*40+col]
                assert fonts[bank][code&127]==glyph
            else:
                if glyph not in fonts[bank]:fonts[bank].append(glyph)
                assert len(fonts[bank])<=124,(level['number'],bank,len(fonts[bank]))
                code=fonts[bank].index(glyph)|selector
            codes.append(code)
        assert len(set(codes))>1,(row,col)
        addr=0x8800+row*40+col
        raw+=bytes((addr&255,addr>>8,period,0,*codes))
        meta.append(dict(role='rail' if slot<6 else 'cabinet' if slot==6 else 'manifold',
                         row=row,col=col,address=addr,period=period,codes=codes))
    return raw,meta

def install_runtime(source):
    f=source/'hardware.s';s=f.read_text()
    a=s.index('background_update:\n');b=s.index('.segment "CODE"\n_music_update',a)
    body=s[a:b].replace('adc #4','adc #8').replace('and #12','and #24').replace('ldx #3','ldx #7')
    body=body.replace('.repeat 2','.repeat 3').replace('resident224B','resident56B')
    body=re.sub(r'anim_frames\+(4|8|12)',lambda m:'anim_frames+'+str(int(m[1])*2),body)
    body=body.replace('.res 4','.res 8').replace('.res 16','.res 32')
    s=s[:a]+body+s[b:]
    s=s.replace('anim_ticks:.res 4','anim_ticks:.res 8').replace('anim_phases:.res 4','anim_phases:.res 8')
    for old,new in ((160,192),(192,224),(224,256),(256,288),(257,289)):
        # Simultaneous replacement below avoids cascading old/new offsets.
        s=s.replace('$9de0+'+str(old)+'\n','$9de0+OFFSET'+str(new)+'\n')
    s=s.replace('OFFSET','')
    # Reuse the two previously unused sound_track/last_track bytes.
    s+='''
.segment "LOADER"
.export _select_music
.import _load_package
_select_music:
    cmp last_track
    beq @ready
    sta _sound_track
    lda #5
    jsr _load_package
    cmp #0
    beq @failed
    lda _sound_track
    sta last_track
@ready:
    lda #1
    ldx #0
    rts
@failed:
    lda #$ff
    sta last_track
    lda #0
    tax
    rts
; Called before asset_load_end, with the complete CRC-checked score resident.
.export _music_reset
_music_reset:
    lda #0
    sta music_row
    sta music_tick
    sta order_index
    sta bass_note
    sta lead_note
    sta drum_type
    rts
'''
    f.write_text(s)
    f=source/'loader.c';s=f.read_text()
    s=s.replace('extern unsigned int loading_done;', 'extern unsigned int loading_done;\nvoid music_reset(void);')
    s=s.replace('if(kind==1)start=1101+', 'if(kind==5)start=512+(unsigned int)sound_track*14;\n    if(kind==1)start=1101+')
    s=s.replace('loaded=kind;ok=1;', 'loaded=kind;if(kind==5)music_reset();ok=1;')
    f.write_text(s)
    f=source/'main.c';s=f.read_text()
    s=s.replace('void menu_select(void);','void menu_select(void);\nunsigned char __fastcall__ select_music(unsigned char area);')
    s=s.replace('if(!load_package(1))return 0;', 'if(!select_music(n/15) || !load_package(1))return 0;',1)
    s=s.replace('if(loaded!=1 && !load_package(1))return 0;', 'if(!select_music(scene/15))return 0;\n    if(loaded!=1 && !load_package(1))return 0;')
    s=s.replace('if(!music_ready){failed_kind=5;if(!load_package(5)){phase=6;show_ui();return;}music_ready=1;}',
                'failed_kind=5;if(!select_music(0)){phase=6;show_ui();return;}music_ready=1;')
    f.write_text(s)
    f=source/'display.c';s=f.read_text().replace('static const unsigned char pf1[4]', 'static const unsigned char pf0[4]={156,188,76,60};\n    static const unsigned char pf1[4]').replace('DESC[536]==238','DESC[536]==pf0[area-1]');f.write_text(s)
    f=source/'validate.c';s=f.read_text().replace('count!=4','count!=8')
    marker='        if(DESC[at+3])return 0;'
    addrs=(0,0,0x8800+22*40+17,0x8800+22*40+8)+tuple(0x8800+r*40+c for r,c,p in EXTRA)
    s=s.replace('    unsigned char i,j,k,w,h,bx,by,count;', '    static const unsigned int light_addr[8]={'+','.join(str(v)+'U' for v in addrs)+'};\n    static const unsigned char light_period[8]={36,36,50,13,23,41,29,61};\n    unsigned char i,j,k,w,h,bx,by,count;')
    a=s.index('        /* Exact authored instrument cells.')
    b=s.index(marker,a)
    s=s[:a]+'''        /* Exact cells/periods; no arbitrary descriptor target is accepted. */
        n=light_addr[i];
        if(i<2){
            n=0x8800U+10*40+37+i;
            if(DESC[541]<=13)n=0x8800U+7*40+7+2*DESC[541]+i;
        }
        if(position!=n || DESC[at+2]!=light_period[i])return 0;
'''+s[b:]
    s=s.replace('for(n=258;n<536;n++)','for(n=290;n<536;n++)')
    f.write_text(s)
