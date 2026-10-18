"""Authored A4 pixel resources; independent expected rasters, no emulator input."""
import json
from pathlib import Path

TITLE = {
 'N':['1100011','1110011','1111011','1101111','1100111','1100011','1100011','1100011','1100011'],
 'E':['1111111','1100000','1100000','1100000','1111100','1100000','1100000','1100000','1111111'],
 'O':['0111110','1100011','1100011','1100011','1100011','1100011','1100011','1100011','0111110'],
 'S':['0111111','1100000','1100000','1100000','0111110','0000011','0000011','0000011','1111110'],
 'H':['1100011','1100011','1100011','1100011','1111111','1100011','1100011','1100011','1100011'],
 'I':['1111111','0011100','0011100','0011100','0011100','0011100','0011100','0011100','1111111'],
 'F':['1111111','1100000','1100000','1100000','1111100','1100000','1100000','1100000','1100000'],
 'T':['1111111','0011100','0011100','0011100','0011100','0011100','0011100','0011100','0011100'],
 '6':['0011110','0110000','1100000','1100000','1111110','1100011','1100011','1100011','0111110'],
 '5':['1111111','1100000','1100000','1100000','1111110','0000011','0000011','0000011','1111110'],
}

def title_pixels():
    p=[[0]*320 for _ in range(20)];text='NEON SHIFT 65'
    width=sum(8 if c==' ' else 16 for c in text)-2;x=(320-width)//2
    for c in text:
        if c==' ':x+=8;continue
        for y,row in enumerate(TITLE[c]):
            for xx,v in enumerate(row):
                if v=='1':
                    for dy in range(2):
                        for dx in range(2):p[y*2+dy][x+xx*2+dx]=1
        x+=16
    for xx in range((320-width)//2,x-2):p[19][xx]=1
    return p

def footer_definition():
    d=json.loads(Path('experiments/eng3-observed-input-3pal/reference/void-loader.json').read_text())
    return dict(font=d['fonts']['anticE3x7Bold'],elements=[e for e in d['elements'] if e.get('name') in ('copyright','studio')],
                commit='ef1924d9690fad3b15f4f9de0474f33140b26799',loader_blob='ca3efe22684f7c9a50a0d0589b7c748657e78eba',generator_blob='792b07949402eaa62ba8c62ba7b5ad461a33bedf')

def footer_pixels():
    d=footer_definition();p=[[0]*320 for _ in range(30)]
    for e in d['elements']:
        x=e['x'];y=e['y']-157
        for c in e['text']:
            if c==' ':x+=d['font']['spaceAdvance']*e['scaleX'];continue
            g=d['font']['glyphs'][c]
            for yy,row in enumerate(g):
                for xx,v in enumerate(row):
                    if v=='1':
                        for dy in range(2):
                            for dx in range(2):p[y+yy*2+dy][x+xx*2+dx]=2
            x+=len(g[0])*2+e['letterSpacing']
    assert all(row[x]==row[x+1] for row in p for x in range(0,320,2))
    return p

# 8 logical pixels map to16 native PAL pixels. Selector bit7 maps pixel3→PF3.
CONTAINER=['00000000','03333330','03222230','03222230','03333330','03200230','03200230','03200230',
           '03200230','03200230','03333330','03222230','03222230','03333330','00000000','00000000']
def container_pixels(docked=False,phase=None):
    p=[[{0:0,2:3,3:1}[int(v)] for v in row] for row in CONTAINER]
    if docked:
        p[14]=[0,2,2,2,2,2,2,0];p[15]=[0,0,2,0,0,2,0,0]
    if phase is not None:
        for x in (1,6):p[2+phase*3][x]=2
    return p
