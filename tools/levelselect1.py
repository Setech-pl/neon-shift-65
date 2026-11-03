"""LEVELSELECT1: a bounded menu overlay, with the normal game/save paths."""
from pathlib import Path
import json,re,subprocess,struct
ROOT=Path(__file__).resolve().parents[1]
def replace(s,old,new):
    assert s.count(old)==1,(old,s.count(old));return s.replace(old,new)
def install(source,out):
    p=source/'main.c';s=p.read_text()
    s=s.replace('void menu_select(void);','void menu_select(void);\nvoid selector_open(void);')
    s=replace(s,'static unsigned char music_ready,game_valid,failed_kind,startup_pending=1,failed_scene,failed_restore,failed_resume;', 'unsigned char game_valid,failed_kind;\nstatic unsigned char music_ready,startup_pending=1,failed_scene,failed_restore,failed_resume;')
    s=replace(s,'static unsigned char prepare(', 'unsigned char prepare(')
    s=replace(s,'static void title(void)', 'void title(void)')
    s=replace(s,'selected=(selected+3)%4','selected=(selected+4)%5')
    s=replace(s,'selected=(selected+1)%4','selected=(selected+1)%5')
    s=replace(s,'else{previous_phase=0;phase=7;show_ui();}', 'else if(selected==3){previous_phase=0;phase=7;show_ui();}\n                else selector_open();')
    s=replace(s,'else if(failed_kind==4)title();', 'else if(failed_kind==4)title();\n                else if(failed_kind==6)selector_open();')
    p.write_text(s)
    p=source/'campaign.c';s=p.read_text();s=replace(s,'static unsigned char save_record[128],save_slot,save_read_ok;', 'unsigned char save_record[128];\nstatic unsigned char save_slot,save_read_ok;');p.write_text(s)
    p=source/'display.c';s=p.read_text().replace('static void text(', 'void text(').replace('static void activate(void)', 'void activate(void)')
    s=replace(s,'for(i=0;i<4;i++)SCREEN[(unsigned int)i*40+11]', 'for(i=0;i<5;i++)SCREEN[(unsigned int)i*40+11]')
    # Five contiguous entries: +2 blank lines before, 8 after. The footer
    # stays at the same scanline and the full list fits its 152-byte buffer.
    s=replace(s,'for(i=0;i<3;i++){DLIST[j++]=0x30;DLIST[j++]=2|(i==2?128:0);}\n    DLIST[j++]=0x50;', 'for(i=0;i<4;i++)DLIST[j++]=2|(i==3?128:0);\n    DLIST[j++]=0x70;')
    s=replace(s,'    DLIST[j++]=0x30;\n    DLIST[j++]=0x42;', '    DLIST[j++]=0x50;\n    DLIST[j++]=0x42;')
    s=replace(s,'text(3,13,"CONFIG");text(selected,11,">");','text(3,13,"CONFIG");text(4,13,"SELECT LEVEL");text(selected,11,">");')
    s=replace(s,'    if(phase==10){','    if(phase==12)return; /* Overlay draws while DMA is still stopped. */\n    if(phase==10){')
    p.write_text(s)
    p=source/'hardware.s';s=replace(p.read_text(),'    sta _hud_pending\n    sta _robot_dirty','    sta _hud_pending\n    sta _selector_seen\n    sta _robot_dirty');p.write_text(s+'\n'+(ROOT/'src/levelselect1/bridge.s').read_text())
    # Link the selector after resident addresses are final, before ATR packing.
    p=source/'build.py';s=p.read_text();s=replace(s,'        atr(name)',"        from levelselect1 import link_overlay\n        link_overlay(OUT,SOURCE)\n        atr(name)");p.write_text(s)

def link_overlay(out,source):
    from selectart1 import make
    make(out)
    subprocess.run(['ca65','-I',str(out),'-o',str(out/'selectart1.o'),str(out/'selectart1.s')],check=True)
    levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
    assert len(levels)==60
    areas=[]
    for n in range(4):
        prefix=levels[n*15]['name'].rsplit(' ',1)[0]
        assert all(l['number']==n*15+i+1 and l['area']==n+1 and l['name']==f'{prefix} {i+1:02}/15' for i,l in enumerate(levels[n*15:n*15+15]))
        areas.append(prefix)
    (out/'selector-areas.h').write_text('static const char * const selector_areas[4]={'+','.join(json.dumps(a) for a in areas)+'};\n')
    # Resolve all shared resident functions/runtime helpers to the final link.
    labels={n:int(a,16) for a,n in re.findall(r'^al (\w+) \.(\w+)',(out/'candidate.lbl').read_text(),re.M)}
    imports=out/'selector-resident.s'
    imports.write_text('\n'.join(('.exportzp ' if a<256 else '.export ')+n+'=$'+format(a,'04x') for n,a in sorted(labels.items()) if not n.startswith("__"))+'\n')
    subprocess.run(['ca65','-o',str(out/'selector-resident.o'),str(imports)],check=True)
    (out/'selector-entry.s').write_text('.segment "ENTRY"\n.import _selector_run\njmp _selector_run\n')
    subprocess.run(['ca65','-o',str(out/'selector-entry.o'),str(out/'selector-entry.s')],check=True)
    subprocess.run(['cl65','-t','atari','-Oirs','-Cl','-g','-I'+str(out),'-I'+str(source),'-I'+str(ROOT/'src'),'-c','-o',str(out/'selector.o'),str(ROOT/'src/levelselect1/selector.c')],check=True)
    (out/'selector.cfg').write_text('''MEMORY { OVERLAY:file=%O,define=yes,start=$A000,size=$0800,fill=yes; }
SEGMENTS { ENTRY:load=OVERLAY,type=ro; CODE:load=OVERLAY,type=ro; RODATA:load=OVERLAY,type=ro;
DATA:load=OVERLAY,type=rw; BSS:load=OVERLAY,type=bss,define=yes; }
''')
    subprocess.run(['cl65','-t','atari','-C',str(out/'selector.cfg'),'-m',str(out/'selector.map'),'-Ln',str(out/'selector.lbl'),'-o',str(out/'selector.bin'),str(out/'selector-entry.o'),str(out/'selector.o'),str(out/'selectart1.o'),str(out/'selector-resident.o')],check=True)
    assert (out/'selector.bin').stat().st_size==2048

def pack(image,out):
    from warehouses import crc16
    from atr import offset
    raw=(out/'selector.bin').read_bytes();assert len(raw)==2048
    at=offset(640,128);assert not any(image[at:at+2176]),'Selector sector collision'
    header=bytearray(128);header[:8]=b'NSLS'+bytes((1,0xa0,0,8));struct.pack_into('<H',header,8,crc16(raw))
    image[at:at+2176]=header+raw
