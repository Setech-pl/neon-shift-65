"""Minimal, bounded splash stream. Post-splash art belongs to the system stage."""
import json,struct,re,subprocess,hashlib
from pathlib import Path

def rec(a,b):return struct.pack('<HH',a,len(b))+b

def make_early(out,source,cmd):
    packs=json.loads((out/'packages.json').read_text())
    splash=(out/'splash.nrq').read_bytes();bitmap=splash[144:144+7680];dl=splash[-202:]
    js="""import fs from 'node:fs';import {packBroadsideLzss,unpackBroadsideLzss} from './experiments/eng3-observed-input-3pal/reference/broadside-lzss.mjs';const raw=fs.readFileSync(process.argv[1]),p=packBroadsideLzss(raw);if(!unpackBroadsideLzss(p).equals(raw))throw Error('roundtrip');fs.writeFileSync(process.argv[2],p);"""
    (out/'splash-bitmap.bin').write_bytes(bitmap)
    cmd('node','--input-type=module','-e',js,out/'splash-bitmap.bin',out/'early-packed.bin')
    packed=(out/'early-packed.bin').read_bytes();assert len(packed)<=0x700,len(packed)
    original=(source/'splash.s').read_text()
    original=original.replace('.import _loading_begin,_loading_label,_loading_progress','').replace('.import _video_clock,_native_dli,_input_rearm,_splash_clock_sync','_video_clock=$17dd')
    a=original.index('    jsr _loading_begin');b=original.index('wait_frame_start:',a)
    original=original[:a]+'''    lda #$40
    sta NMIEN
    lda saved_dli
    sta $200
    lda saved_dli+1
    sta $201
    lda #3
    sta $d20f
    plp
    rts
saved_dli:.word 0
'''+original[b:]
    original=original.replace('    php\n    sei','    lda $200\n    sta saved_dli\n    lda $201\n    sta saved_dli+1\n    php\n    sei')
    original=original[:original.index('.include "cache.s"')]
    a=original.index('@release:');b=original.index('; -----------------------------------------------------------------------------\n; Bit cells',a)
    original=original[:a]+'    rts\n\n'+original[b:]
    (out/'early-splash.s').write_text(original)
    # Early support lives at0600 until LOW is loaded after its final return.
    support=(source/'early-support.s').read_text().replace('PACKED_BYTES',str(len(packed)))
    (out/'early-support.s').write_text(support)
    cfg=f'''MEMORY {{ EARLY:file="{out}/early-code.bin",start=$0600,size=$0800; SPLASH:file="{out}/early-splash.bin",start=$9400,size=$0400; }}
SEGMENTS {{ CODE:load=EARLY,type=ro; SPLASH:load=SPLASH,type=rw; }}'''
    (out/'early.cfg').write_text(cfg)
    for name in ['early-support','early-splash']:
        cmd('ca65','-g','-I',out,'-o',out/(name+'.o'),out/(name+'.s'))
    cmd('ld65','-C',out/'early.cfg','-Ln',out/'early.lbl','-m',out/'early.map',out/'early-support.o',out/'early-splash.o')
    labels={m[2]:int(m[1],16) for m in re.finditer(r'al (\w+) \.([\w]+)',(out/'early.lbl').read_text())}
    early=rec(0x600,(out/'early-code.bin').read_bytes())+rec(0x9400,(out/'early-splash.bin').read_bytes())+rec(0x8c00,packed)+rec(0x8800,dl)
    # Pad before sentinel so no sector read before splash contains system payload.
    pad=(-len(early)-8)%128
    early+=rec(0x9300,bytes(pad))+struct.pack('<HH',0x600,0)
    assert len(early)%128==0
    # Loader art160x64 (320 native colour clocks,64 native scanlines).
    import loading_art
    art=loading_art.generate(out)
    cmd('ca65','-o',out/'loading-text.o',source/'loading-text.s')
    cfg=f'MEMORY {{ TEXT:file="{out}/early-text.bin",start=$9240,size=$00c0; }} SEGMENTS {{ CODE:load=TEXT,type=rw; }}'
    (out/'early-text.cfg').write_text(cfg);cmd('ld65','-C',out/'early-text.cfg','-o',out/'early-text.bin',out/'loading-text.o')
    # Shared RAM total includes every unique successful sector and validation readiness.
    # Early/post split is byte packed: count the sector containing the sentinel only once.
    # Resident count is stable across variants; actual total written after stream assembly in build.py.
    status=bytearray(224);
    status[0:19]=bytes(ord(c)-32 for c in 'READ ERROR         ')
    status[0x24:0x24+len('INITIALIZING SYSTEM')]=bytes(ord(c)-32 for c in 'INITIALIZING SYSTEM')
    for row in [0x48,0x70]:status[row+4:row+36]=bytes([0x55]*32)
    status[0x4c]|=0x80
    status[0x74]|=0x80
    status[0xbf]=0x65
    late=rec(0xba00,art)+rec(0xbf00,loading_art.display_list())+rec(0x9240,(out/'early-text.bin').read_bytes())+rec(0x1720,bytes(status))+struct.pack('<HH',labels['early_ui'],0)
    # Persistent metadata for pre-splash sector bound and payload attribution.
    (out/'early-budget.json').write_text(json.dumps(dict(early_bytes=len(early),early_sectors=(len(early)+127)//128,packed_bitmap_bytes=len(packed),raw_bitmap_bytes=7680,code_bytes=(out/'early-code.bin').stat().st_size,splash_code_bytes=(out/'early-splash.bin').stat().st_size,late_loader_bytes=len(late),labels=labels),indent=2)+'\n')
    assert (len(early)+127)//128<=32,'bootstrap budget exceeded'
    return early+late
