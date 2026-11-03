"""Campaign art slot: 160x64 ANTIC C,1280 B; replace independently per area."""
import json,sys
from pathlib import Path
sys.path.insert(0,'tools')
from assets import png

def generate(out):
    p=[[0]*160 for _ in range(64)]
    def line(x,y,a,b):
        n=max(abs(a-x),abs(b-y))
        for i in range(n+1):
            xx=x+(a-x)*i//max(1,n);yy=y+(b-y)*i//max(1,n)
            if 0<=xx<160 and 0<=yy<64:p[yy][xx]=1
    def box(x,y,w,h):
        for a,b,c,d in [(x,y,x+w-1,y),(x,y,x,y+h-1),(x+w-1,y,x+w-1,y+h-1),(x,y+h-1,x+w-1,y+h-1)]:line(a,b,c,d)
    # Room perspective, side rails, overhead utility and central doorway.
    box(16,8,128,42);box(19,11,122,36)
    for x in [0,159]:line(x,0,16 if x==0 else 143,8);line(x,63,16 if x==0 else 143,49)
    for x in [16,42,118,143]:line(x,50,max(0,min(159,80+(x-80)*2)),63)
    line(0,57,159,57);line(0,2,159,2)
    box(55,13,50,30);box(58,16,44,27)
    # Tall equipment rack, terminal, cable ducts and fan.
    box(23,17,20,31)
    for y in [20,28,36]:box(26,y,14,5);line(28,y+2,34,y+2)
    box(113,26,23,21);box(116,29,17,9);line(118,32,127,32);line(118,35,123,35)
    line(125,17,125,25);box(117,13,17,9);line(120,15,130,20);line(130,15,120,20)
    # Recognizable service robot: sensor head, chassis, arms and two tread bases.
    box(70,27,20,10);box(73,30,14,3);line(80,22,80,26);line(78,22,82,22)
    box(66,37,28,15);box(73,40,14,8);line(77,43,83,43)
    box(63,50,12,8);box(85,50,12,8)
    for y in [52,55]:line(65,y,72,y);line(87,y,94,y)
    line(66,39,59,44);line(59,44,59,51);line(94,39,102,44);line(102,44,102,51);line(101,51,109,54);line(101,53,108,56)
    raw=bytes(sum(p[y][x+i]<<(7-i) for i in range(8)) for y in range(64) for x in range(0,160,8))
    import themes,compile
    if themes.AREA!=1:raw=themes.loading(compile)
    p=[[((raw[y*20+x//8]>>(7-x%8))&1) for x in range(160)] for y in range(64)]
    assert len(raw)==1280
    png(out/'loading-art-native.png',[[v for v in row for _ in range(2)] for row in p],[(0,0,0),(220,240,240)],1)
    (out/'loading-art.json').write_text(json.dumps(dict(area=themes.AREA,slot=[0xba00,0xbf00],mode='ANTIC C',pixels=[320,64],native_scanlines=64,replace='generate() or independent exact1280-byte area bitmap'),indent=2)+'\n')
    return raw

def display_list():
    # Normal320-wide raster: y0..63 blank, y64..127 art, bottom label at176.
    dl=bytearray([0x70]*8+[0x4c,0,0xba]+[0x0c]*63+[0x70]*6+[0x4f,0x00,0x91]+[0x0f]*7+[0x30,0x4f,0x68,0x17,0x0f,0x41,0x00,0xbf])
    assert len(dl)<=128 # ANTIC C actually displays2scanlines/instruction? corrected below.
    return dl
