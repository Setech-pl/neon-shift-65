#!/usr/bin/env python3
"""WINDOWED launcher and short hardware paths; --check never opens a GUI."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'build/owner-smoke/hwvis1';AT=16+8099*128

def route_disk(number,source,dest):
    """Prepare a valid penultimate state on a disposable copy, using disk ABI."""
    levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
    level=levels[number-1];rows=level['rows'];path=level['path']
    p=next((x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '@+')
    boxes=[(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '$*'];pushes=0
    for c in path[:-1]:
        dx,dy={'U':(0,-1),'D':(0,1),'L':(-1,0),'R':(1,0)}[c];q=p[0]+dx,p[1]+dy
        assert rows[q[1]][q[0]]!='#'
        if q in boxes:
            z=q[0]+dx,q[1]+dy;assert z not in boxes and rows[z[1]][z[0]]!='#'
            boxes[boxes.index(q)]=z;pushes+=1
        p=q
    from warehouses import crc16
    image=bytearray(source.read_bytes());record=bytearray(128);record[:4]=b'NSAV'
    record[4:10]=bytes([1,number-1,3,0,1,0])
    record[10:14]=hashlib.sha256((ROOT/'assets/levels/camp2-b/campaign.json').read_bytes()).digest()[:4]
    board=16+(1100+(number-1)*70-1)*128
    record[14:16]=image[board+126:board+128];record[16:19]=bytes([*p,len(boxes)])
    record[19:19+len(boxes)*2]=bytes(v for b in boxes for v in b)
    record[39:43]=(len(path)-1).to_bytes(4,'little');record[43:47]=pushes.to_bytes(4,'little')
    record[126:]=crc16(record[:126]).to_bytes(2,'little')
    image[AT:AT+256]=record+bytes(128);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(image)
    return dict(level=number,last_move=path[-1],cold_boot='CONTINUE',then='release, last direction, release, FIRE',sha256=hashlib.sha256(image).hexdigest(),path=str(dest))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--area',type=int,choices=(1,16,31,46));p.add_argument('--route',type=int,choices=(15,30,45,60))
    p.add_argument('--prepare-routes',action='store_true');p.add_argument('--check',action='store_true')
    p.add_argument('--emulator',default=os.environ.get('NEON_ATARI800') or shutil.which('atari800'))
    p.add_argument('--config',default=os.environ.get('NEON_ATARI_CONFIG'))
    p.add_argument('--physical-joystick',action='store_true');a=p.parse_args()
    if not a.prepare_routes and (not a.emulator or not a.config):p.error('Set NEON_ATARI800 and NEON_ATARI_CONFIG, or pass --emulator and --config; supply your own legal ROM config.')
    subprocess.run([sys.executable,str(ROOT/'tools/hwvis1_prepare.py')],check=True)
    normal=ROOT/'dist/neon-shift65-v1.0.0.atr';routes=DOC/'routes'
    if a.prepare_routes:
        records=[route_disk(n,normal,routes/f'smoke-level-{n:02}.atr') for n in (15,30,45,60)]
        (routes/'routes.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2));return 0
    if a.area and a.route:p.error('Choose --area or --route')
    name=f'area-{a.area:02}' if a.area else f'route-{a.route:02}' if a.route else 'normal'
    atr=DOC/f'neon-shift65-hwvis1-test-{a.area:02}.atr' if a.area else normal
    if a.route:
        atr=routes/f'smoke-level-{a.route:02}.atr';print(json.dumps(route_disk(a.route,normal,atr),indent=2))
    cmd=[sys.executable,str(ROOT/'tools/product1_owner_smoke.py'),'--atr',str(atr),
         '--emulator',a.emulator,
         '--config',a.config,
         '--output',str(DOC/'play'/name)]
    if a.check:cmd.append('--check')
    if a.physical_joystick:cmd.append('--physical-joystick')
    return subprocess.call(cmd)

if __name__=='__main__':raise SystemExit(main())
