#!/usr/bin/env python3
"""Lossless screenshot copies, integer replication and externally labelled pairs."""
import hashlib
import json
import shutil
import struct
import sys
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments/renderer-a5c'))
from verify import png

DEST=ROOT/'docs/recovery1/screenshots'
FONT=json.loads((ROOT/'assets/graphics/mono-font.json').read_text())['hud_rows']


def write_rgb(path, rows):
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
    w,h=len(rows[0]),len(rows)
    raw=b''.join(b'\0'+bytes(v for rgb in row for v in rgb) for row in rows)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def rgb(path):
    data,pal=png(path)
    return [[tuple(pal[v]) for v in row] for row in data]


def pair(name, left, right):
    scale=3;gap=12;header=36;w=336*scale;h=240*scale
    canvas=[[(16,24,32)]*(w*2+gap) for _ in range(h+header)]
    for i,(label,path) in enumerate((left,right)):
        data=rgb(path)
        for y,row in enumerate(data):
            line=[v for v in row for _ in range(scale)]
            for dy in range(scale):canvas[header+y*scale+dy][i*(w+gap):i*(w+gap)+w]=line
        for n,ch in enumerate(label.upper()):
            for y,row in enumerate(FONT.get(ch,'000000/000000/000000/000000/000000/000000/000000').split('/')):
                for x,v in enumerate(row):
                    if v=='1':
                        for yy in range(2):
                            for xx in range(2):canvas[8+y*2+yy][i*(w+gap)+10+n*14+x*2+xx]=(230,235,240)
    write_rgb(DEST/(name+'-3x.png'),canvas)


def copy(source,name,manifest):
    dest=DEST/(name+'-native.png');shutil.copyfile(source,dest)
    manifest.append(dict(file=str(dest.relative_to(ROOT)),source=str(source.relative_to(ROOT)),
                         sha256=hashlib.sha256(source.read_bytes()).hexdigest(),method='Unmodified native Atari800 screenshot'))
    return dest


def main():
    DEST.mkdir(parents=True,exist_ok=True);manifest=[];service={}
    for v in ('art21','vis1r2','visual2','art4A','art4B'):
        service[v]=copy(ROOT/f'build/recovery1/service-{v}/capture/native-0950.png','service-'+v,manifest)
    for v in ('art21','visual2','art4A','art4B'):
        pair('service-'+v+'-vs-recovered',(v+' SERVICE 20X10',service[v]),('VIS1-R2 SERVICE 20X10',service['vis1r2']))
    records=json.loads((ROOT/'build/recovery1/large-comparison.json').read_text())['records']
    large={r['variant']:copy(ROOT/r['native'],'energy09-'+r['variant'],manifest) for r in records}
    for v in ('camp2b-current','art4A-current','art4B-current'):
        pair('energy09-'+v+'-vs-recovered',(v+' ENERGY09',large[v]),('VIS1-R2 ENERGY09',large['camp2b-recovered']))
    # Actual owner campaign, identical geometry/current art vs recovered art.
    owner={}
    for v in ('owner-visual2','owner-vis1r2'):
        b=ROOT/'build/recovery1'/v
        run=json.loads((b/'campaign-full/campaign-result.json').read_text())['levels'][8]
        frame=run['frame']-run['moves']*8-15
        owner[v]=copy(b/f'campaign-full/native-{frame:04}.png','owner-energy09-'+v,manifest)
    pair('owner-energy09-current-vs-recovered',('OWNER SOURCE VISUAL2',owner['owner-visual2']),('OWNER SOURCE VIS1-R2',owner['owner-vis1r2']))
    (ROOT/'docs/recovery1/screenshots.json').write_text(json.dumps(dict(native=manifest,comparisons='3x integer pixel replication; labels outside native frames; no RGB edits, retouching or synthetic tiles'),indent=2)+'\n')


if __name__=='__main__':main()
