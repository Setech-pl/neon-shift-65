"""Original ANTIC4 industrial illustration vocabulary and scene compositions.
Each fragment is 4x8 colour pixels. Deliberate geometry, no image resampling.
32 unique fragments plus four oscilloscope frames fit glyphs 92..127.
"""
from pathlib import Path
import json

def compile_scenes(chars):
    # Gray PF3 only: scene codes carry bit7; board codes retain colorful PF2.
    rows=[
      ['0000']*8, ['3333']*8,
      ['0000','0000','0000','0330','0330','0000','0000','0000'], # dim lamp
      ['3333','3333','3300','3300','3300','3300','3300','3300'],
      ['3333','3333','0033','0033','0033','0033','0033','0033'],
      ['3300','3300','3300','3300','3300','3300','3333','3333'],
      ['0033','0033','0033','0033','0033','0033','3333','3333'],
      ['0330']*8, ['0000','0000','0000','3333','3333','0000','0000','0000'],
      ['3333','0000','0000','0000','0000','0000','0000','0000'],
      ['0000','0000','0000','0000','0000','0000','0000','3333'],
      ['0300']*8, ['0030']*8,
      ['0000','0003','0033','0333','3333','3333','3333','3333'],
      ['0000','3000','3300','3330','3333','3333','3333','3333'],
      ['3333','3333','3333','3333','0333','0033','0003','0000'],
      ['3333','3333','3333','3333','3330','3300','3000','0000'],
      ['0000','0000','3333','0000','3333','0000','3333','0000'],
      ['0000','0000','0220','0220','0000','0000','0000','0000'],
      ['0000','0000','0000','3000','0300','0030','0003','0000'],
      ['0000','0000','0000','0003','0030','0300','3000','0000'],
      ['3300','0330','0033','0003','0003','0003','0003','0003'],
      ['0033','0330','3300','3000','3000','3000','3000','3000'],
      ['1111','1001','1001','1001','1001','1001','1001','1111'],
      ['0000','0000','0000','0100','0010','0000','0000','0000'],
      ['3333','3333','0000','0000','2222','0000','3333','3333'],
      ['3333','3333','0000','0000','0000','0000','3333','3333'],
      ['3333','3003','0330','3003','0330','3003','0330','3333'],
      ['3333','0000','0030','0000','3000','0000','0000','3333'],
      ['0300','0030','0300','0030','0300','0030','0300','0030'],
      ['0000','0000','0000','0000','0033','0330','3300','0000'],
      ['0000','0000','0000','0000','3300','0330','0033','0000'],
    ]
    # Prepared dotted sinusoid slices. No arithmetic in the game ISR.
    for ys in [(4,2,1,2),(1,2,4,6),(4,6,7,6),(7,6,4,2)]:
        g=[['0']*4 for _ in range(8)]
        for x,y in enumerate(ys):g[y][x]='3'
        rows.append([''.join(r) for r in g])
    assert len(rows)==36
    rows=[[''.join('3' if c!='0' else '0' for c in r) for r in g] for g in rows]
    # Dim broad silhouette fills, retaining outlines and isolated small lights.
    # Dither is authored at the 4x8 color-pixel fragment raster, never smoothed.
    for i,g in enumerate(rows):
        source=g[:]
        for y in range(8):
            for x in range(4):
                if (x+y)&1 and source[y][x]=='3' and all(source[yy][xx]=='3'
                    for yy,xx in ((max(0,y-1),x),(min(7,y+1),x),(y,max(0,x-1)),(y,min(3,x+1)))):
                    g[y]=g[y][:x]+'0'+g[y][x+1:]
    for i,g in enumerate(rows):chars[(92+i)*8:(93+i)*8]=[sum(int(c)<<(6-2*x) for x,c in enumerate(r)) for r in g]
    def make(variant):
        m=[0]*880
        def at(x,y,k):
            if 0<=x<40 and 0<=y<22:m[y*40+x]=(92+k)|128
        def fill(x,y,w,h,k):
            for yy in range(y,y+h):
                for xx in range(x,x+w):at(xx,yy,k)
        def panel(x,y,w,h):
            fill(x,y,w,1,9);fill(x,y+h-1,w,1,10);fill(x,y,1,h,11);fill(x+w-1,y,1,h,12)
            at(x,y,3);at(x+w-1,y,4);at(x,y+h-1,5);at(x+w-1,y+h-1,6)
        # Gantry overhead, diagonal cables, far wall. No floor-like lattice.
        fill(0,0,40,1,8);fill(0,2,12,1,9);fill(29,2,11,1,9)
        for i in range(5):at(19+i,i+1,19)
        for i in range(4):at(27-i,i+1,20)
        # Large industrial robot: broad shoulder, dark visor, neck, torso,
        # jointed handling arm, and two caterpillar tracks along lower edge.
        fill(1,4,7,1,13);fill(1,5,8,3,1);at(8,4,14)
        fill(2,6,5,1,25);fill(4,8,3,2,7)
        fill(0,10,10,6,1);fill(1,11,8,4,0);fill(2,12,2,2,23)
        fill(6,11,2,3,17);at(8,14,24)
        fill(9,10,4,2,8);fill(12,11,2,4,7);fill(13,14,3,1,8)
        at(15,13,3);at(15,14,5)
        fill(0,16,3,3,27);fill(7,16,4,3,27)
        fill(0,19,11,1,10)
        # Equipment bay: oscilloscope enclosure, vents, conduits, status rack.
        panel(30,5,9,8);fill(32,7,5,1,17);fill(32,10,4,1,26)
        panel(28,15,12,7);fill(30,17,7,1,17);fill(30,19,7,1,26)
        fill(38,0,1,5,29);fill(29,12,1,4,7);at(29,14,21)
        fill(13,20,12,1,8);at(12,19,30);at(25,19,31)
        if variant:
            # Same vocabulary, distinct gantry/control cabinet arrangement.
            panel(17,2,9,4);fill(19,4,5,1,17)
            fill(32,14,5,1,8);fill(35,13,1,2,7)
            at(4,12,24);at(6,13,24)
        return m
    maps=[make(0),make(1)]
    Path('build/scenes-source.json').write_text(json.dumps(dict(fragments=rows,maps=maps)))
    return maps
