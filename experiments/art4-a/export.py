#!/usr/bin/env python3
"""Export the authored procedural sources as inspectable logical pixel rows."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from assets import encode_tile,decode_tile
from art import Art


def blank(w=8,h=16):return [[0]*w for _ in range(h)]
def rect(p,x,y,w,h,value):
    for yy in range(max(0,y),min(len(p),y+h)):
        for xx in range(max(0,x),min(len(p[0]),x+w)):p[yy][xx]=value
def line(p,x,y,xx,yy,value):
    n=max(abs(xx-x),abs(yy-y))
    for i in range(n+1):
        a=x+(xx-x)*i//max(1,n);b=y+(yy-y)*i//max(1,n)
        if 0<=b<len(p) and 0<=a<len(p[0]):p[b][a]=value
def rows(p):return [''.join(map(str,row)) for row in p]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='assets/graphics/art4-a');a=parser.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    c=SimpleNamespace(blank=blank,rect=rect,line=line,tile=lambda p:bytes(encode_tile(p)))
    for direction in ('A','B'):
        art=Art(direction);art.resources(c)
        robots=art.robot_frames()
        data=dict(stage='ART4-A',direction=direction,status='OWNER_PENDING',
            authoritative_source='experiments/art4-a/art.py',format='logical 2-bit pixel rows; tile 8x16, glyph4x8; no upsampling',
            palette=dict(zip(('PF0','PF1','PF2','PF3','BK'),art.PALETTE)),
            selector='normal pixel3=PF2; inverse glyph pixel3=PF3; other pixels retain same color registers',
            walls=[dict(mask=m,kind=k,pixels=rows(decode_tile(art.wall(m,k)))) for m in range(16) for k in (0,1,2,3,19,35,51,4)],
            floors=[rows(decode_tile(t)) for t in art.floors()],dock=rows(art.dock()),
            container=rows(art.container()),docked=rows(art.container(True)),dock_flash=[rows(art.container(True,k)) for k in range(3)],
            robots=[dict(substrate=i//20,direction=('up','down','right','left')[(i%20)//5],mode=i%5,
                         pixels=rows(decode_tile(robots[i*32:i*32+32]))) for i in range(40)],
            devices={kind:[rows(art.device(kind,phase)) for phase in range(4)] for kind in ('terminal','cabinet','fan','gate','installation')})
        (out/f'{direction}.json').write_text(json.dumps(data,indent=2)+'\n')
    print('PASS exported exact logical source pixels A/B')


if __name__=='__main__':main()
