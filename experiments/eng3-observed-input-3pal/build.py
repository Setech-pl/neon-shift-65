#!/usr/bin/env python3
"""Isolated cc65 build, real linker map and bootable candidate ATR."""
import hashlib,json,re,struct,subprocess,sys,shutil,os
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from atr import chunks,empty_atr,offset
from warehouses import crc16
from compile import OUT,SOURCE

def cmd(*args):
    args=list(map(str,args))
    # cl65 creates temporary .s beside its C input. Give each output directory
    # its own C inputs so independent area builds cannot race on source paths.
    if args[0]=='cl65' and '-c' in args and args[-1].endswith('.c'):
        local=OUT/'cc-input'/Path(args[-1]).name;local.parent.mkdir(exist_ok=True)
        shutil.copyfile(args[-1],local);args[-1]=str(local)
    subprocess.run(args,check=True)
def main():
    shutil.copytree(SOURCE/'reference',OUT/'reference',dirs_exist_ok=True)
    cmd(sys.executable,SOURCE/'compile.py')
    obj=OUT/'obj';obj.mkdir(exist_ok=True)
    parser=Path('src/level.c').read_text()
    parser=parser.replace('static unsigned char connected[MAX_LEVEL_HEIGHT][MAX_LEVEL_WIDTH];',
      '#ifdef __ATARI__\n#define connected (*(unsigned char (*)[20][38])0xa000)\n#else\nstatic unsigned char connected[MAX_LEVEL_HEIGHT][MAX_LEVEL_WIDTH];\n#endif')
    parser=parser.replace('static Point frontier[MAX_LEVEL_WIDTH * MAX_LEVEL_HEIGHT];',
      '#ifdef __ATARI__\n#define frontier ((Point *)0xa2f8)\n#else\nstatic Point frontier[MAX_LEVEL_WIDTH * MAX_LEVEL_HEIGHT];\n#endif')
    begin=parser.index('unsigned char level_try_move(');end=parser.index('unsigned char level_is_solved(',begin)
    parser=parser[:begin]+'#if !defined(__ATARI__) && !defined(NATIVE_MOVE)\n'+parser[begin:end]+'#endif\n'+parser[end:]
    (OUT/'level.c').write_text(parser)
    fast_undo=True
    undo=Path('src/undo.c').read_text()
    if fast_undo:
        undo=undo.replace('static unsigned char history','unsigned char history').replace('static unsigned int count','unsigned int count').replace('static unsigned int capacity','unsigned int capacity').replace('static unsigned char head','unsigned char head')
        undo=undo.replace('unsigned char undo_pop(GameState *gs)', '#if !defined(__ATARI__) && !defined(NATIVE_MOVE)\nunsigned char undo_pop(GameState *gs)')+'\n#if defined(__ATARI__) || defined(NATIVE_MOVE)\n#else\n#endif\n'
        # Close only the function exclusion, preserving C host oracle.
        undo=undo[:undo.rfind('#if defined(__ATARI__)')]+'#endif\n'
    (OUT/'undo.c').write_text(undo)
    (OUT/'aliases.s').write_text('.export _sector_buffer=$9c00\n.export _robot_frames=$b160\n.import _phase\n.export _flow=_phase\n')
    files=[SOURCE/'display.c',SOURCE/'loader.c',OUT/'level.c',OUT/'assets.c',Path('src/game.c'),(OUT/'undo.c'),SOURCE/'input.c',SOURCE/'input_atari.c']
    objects=[]
    flags=['-t','atari','-Oirs','-Cl','-g','-I'+str(OUT),'-I'+str(SOURCE),'-Isrc']
    for p in files:
        dest=obj/(p.stem+'.o');cmd('cl65',*flags,'-c','-o',dest,p);objects.append(dest)
    dest=obj/'validate.o';cmd('cl65',*[f for f in flags if f!='-Oirs'],'-c','-o',dest,SOURCE/'validate.c');objects.append(dest)
    for p in [SOURCE/'loading.s',SOURCE/'hardware.s',SOURCE/'render.s',SOURCE/'header.s',SOURCE/'sio.s',SOURCE/'crc.s',SOURCE/'move.s',SOURCE/'phase.s',SOURCE/'regions.s',OUT/'aliases.s',OUT/'numfont.s']:
        dest=obj/(p.stem+'.o');cmd('ca65','-t','atari','-g','-I',OUT,'-I',SOURCE,'-o',dest,p);objects.append(dest)
    if fast_undo:
        dest=obj/'undo-fast.o';cmd('ca65','-g','-o',dest,SOURCE/'undo-fast.s');objects.append(dest)
    cmd('ca65','-I',SOURCE,'-o',obj/'boot.o',SOURCE/'boot.s')
    cmd('ld65','-C',SOURCE/'boot.cfg','-Ln',OUT/'boot.lbl','-o',OUT/'boot.bin',obj/'boot.o')
    for name,define in [('candidate',None),('dim','DIM'),('stress','STRESS'),('carry','CARRY'),('wrap','WRAP'),('counter9','COUNTER_START=9'),('counter99','COUNTER_START=99'),('counter999','COUNTER_START=999')]:
        main_obj=obj/(name+'-main.o')
        cmd('cl65',*flags,*(['-D'+define] if define else []),'-c','-o',main_obj,SOURCE/'main.c')
        cmd('cl65','-t','atari','-C',SOURCE/'link.cfg','-m',OUT/(name+'.map'),'-Ln',OUT/(name+'.lbl'),'-o',OUT/(name+'.xex'),main_obj,*objects)
        atr(name)
    # One replay through host sanitizer and one through6502 cc65 real logic.
    common=[OUT/'replay.c',OUT/'assets.c',OUT/'level.c',Path('src/game.c'),(OUT/'undo.c')]
    cmd('clang','-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-g','-I'+str(OUT),'-Isrc',*common,'-o',OUT/'replay-host')
    cmd(OUT/'replay-host')
    simobj=[]
    for i,p in enumerate(common):
        o=obj/f'sim-{i}.o';cmd('cl65','-t','sim6502','-DNATIVE_MOVE','-Oirs','-Cl','-I'+str(OUT),'-Isrc','-c','-o',o,p);simobj.append(o)
    cmd('ca65','-t','sim6502','-DNATIVE_SIM65','-o',obj/'sim-move.o',SOURCE/'move.s')
    simobj.append(obj/'sim-move.o')
    if fast_undo:
        cmd('ca65','-o',obj/'sim-undo.o',SOURCE/'undo-fast.s');simobj.append(obj/'sim-undo.o')
    cmd('cl65','-t','sim6502','-o',OUT/'replay-target',*simobj);cmd('sim65',OUT/'replay-target')
    print('PASS isolated candidate build, ATR, sanitizer + real6502 replay')

def atr(name):
    image=empty_atr(8192,128);image[16:400]=(OUT/'boot.bin').read_bytes()
    records,entry=chunks((OUT/(name+'.xex')).read_bytes())
    stream=b''.join(struct.pack('<HH',addr,len(data))+data for addr,data in records)+struct.pack('<HH',entry,0)
    from early import make_early
    early_stream=make_early(OUT,SOURCE,cmd)
    program_sectors=(len(stream)+127)//128
    stream=early_stream+stream
    early_budget=json.loads((OUT/'early-budget.json').read_text())
    pre_splash_sectors=early_budget['early_sectors']
    total_system_sectors=(len(stream)+127)//128-pre_splash_sectors
    # Catalog cached once, music14+menu50 sectors,2 CRC validation units,1 init.
    total_work=total_system_sectors+1+sum((p['bytes']+127)//128 for p in json.loads((OUT/'packages.json').read_text()) if p['kind'] in (4,5))+3
    marker=stream.index(struct.pack('<HH',0x1720,224))+4
    stream=bytearray(stream)
    struct.pack_into('<H',stream,marker+0xb2,total_work)
    struct.pack_into('<H',stream,marker+0xb0,(marker+0xb0)//128+1-early_budget['early_sectors'])
    stream=bytes(stream)
    with (OUT/(name+'.lbl')).open('a') as f:f.write((OUT/'early.lbl').read_text())
    stride=1
    stride_addr=int(re.search(r'al ([0-9A-Fa-f]+) .progress_stride', (OUT/'boot.lbl').read_text())[1],16)
    image[16+stride_addr-0x9800]=stride
    assert len(stream)<495*128
    image[offset(5,128):offset(5,128)+len(stream)]=stream
    directory=bytearray(128);directory[:6]=b'NSRD\2\5'
    packs=[p for p in json.loads((OUT/'packages.json').read_text()) if p['kind']<=5]
    starts=[512,640,768,896,960]
    for i,(p,start) in enumerate(zip(packs,starts)):
        data=(OUT/(p['name']+'.nrq')).read_bytes();count=(len(data)+127)//128
        assert start+count<= (starts+[8193])[i+1]
        image[offset(start,128):offset(start,128)+len(data)]=data
        struct.pack_into('<BB6H',directory,16+i*16,p['kind'],0,start,count,len(data),crc16(data),0,0)
    struct.pack_into('<H',directory,126,crc16(directory[:126]));image[offset(4,128):offset(4,128)+128]=directory
    path=OUT/(name+'.atr');path.write_bytes(image)
    (OUT/(name+'-atr.json')).write_text(json.dumps(dict(program_bytes=len(stream),resident_program_sectors=program_sectors,system_work=total_work,early=early_budget,program_sectors=(len(stream)+127)//128,boot_entry=entry,package_starts=starts,sha256=hashlib.sha256(image).hexdigest(),atr=str(path)),indent=2)+'\n')

if __name__=='__main__':main()
