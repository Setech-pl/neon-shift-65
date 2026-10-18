#!/usr/bin/env python3
"""Compile campaign geometry into existing per-strip NSRQ packages."""
import hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]);out=Path(os.environ['NEON_ART2_BUILD']);area=int(os.environ['NEON_ART2_AREA'])
sys.path.insert(0,str(source))
import compile as c
spec=importlib.util.spec_from_file_location('product_art',ROOT/'experiments/product1/art.py');art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
a=c.arrays()
# Same historical fixture before/after, same absolute geometry and settings.
before=out/'comparison-before';after=out/'comparison-after'
before.mkdir();after.mkdir()
c.scene(c.levels()[0],0,a)
for f in out.glob('scene-0*'):shutil.copyfile(f,before/f.name)
art.install(c)
c.scene(c.levels()[0],0,a)
for f in out.glob('scene-0*'):shutil.copyfile(f,after/f.name)
from product1_data import load
raw,levels=load()
if os.environ.get('NEON_VISUAL2')=='1' and area==1:
    spec=importlib.util.spec_from_file_location('visual2',ROOT/'experiments/product1/visual2.py')
    visual2=importlib.util.module_from_spec(spec);spec.loader.exec_module(visual2)
    direction=os.environ.get('NEON_ART4')
    if direction:
        spec=importlib.util.spec_from_file_location('art4',ROOT/'experiments/art4-a/art.py')
        art4=importlib.util.module_from_spec(spec);spec.loader.exec_module(art4)
        visual2.install(c,art4.Art(direction))
    else:visual2.install(c)
if os.environ.get('NEON_ART_FINAL')=='1' and area==1:
    spec=importlib.util.spec_from_file_location('art_final',ROOT/'experiments/art-final/energy.py')
    art_final=importlib.util.module_from_spec(spec);spec.loader.exec_module(art_final)
    art_final.install(c)
if os.environ.get('NEON_FINISH1')=='1':
    spec=importlib.util.spec_from_file_location('finish1_art',ROOT/'experiments/finish1/art.py')
    finish1=importlib.util.module_from_spec(spec);spec.loader.exec_module(finish1)
    finish1.install(c)
if os.environ.get('NEON_FINISH2')=='1':
    spec=importlib.util.spec_from_file_location('finish2_art',ROOT/'experiments/finish2/art.py')
    finish2=importlib.util.module_from_spec(spec);spec.loader.exec_module(finish2)
    finish2.install(c)
if os.environ.get('NEON_RELEASE1')=='1':
    spec=importlib.util.spec_from_file_location('release1_art',ROOT/'experiments/release1/art.py')
    release1=importlib.util.module_from_spec(spec);spec.loader.exec_module(release1)
    release1.install(c)
previous_devices=c.decoration.devices
def campaign_devices(old,number,level):
    rows=level['rows'];occupied=set();result=[]
    floor=[(x,y) for y,r in enumerate(rows) for x,ch in enumerate(r) if ch!='#']
    for kind,_,_,period,phase in old:
        parts=list(c.split(c.device(kind,0)));candidates=[]
        for y in range(-1,8):
            for x in range(-1,17):
                cells={(x+dx,y+dy) for dx,dy in parts}
                if any(not(-2<=xx<=17 and -1<=yy<=8) or (xx,yy) in occupied or
                       (0<=xx<16 and 0<=yy<8 and rows[yy][xx]!='#') for xx,yy in cells):continue
                if not any(0<=xx<16 and 0<=yy<8 for xx,yy in cells):continue
                distance=min(abs(x-xx)+abs(y-yy) for xx,yy in floor)
                candidates.append((distance,-abs(x-14),-abs(y-4),x,y,cells))
        assert candidates,('no wall-owned device placement',kind,level['name'])
        _,_,_,x,y,cells=max(candidates);occupied.update(cells);result.append((kind,x,y,period,phase))
    # VIS1-r2's wall-section plan is constructed by its existing selector.
    if c.themes.AREA==1:
        saved=c.decoration.devices
        # Its wrapper calls the base selector, currently frozen in closure;
        # provide the selected wall-only coordinates as the old positions.
        return previous_devices(result,number,level)
    return result
c.decoration.devices=campaign_devices
for l in (l for l in levels if l['area']==area):
    c.scene(l,0,a)
    folder=out/f"level-{l['number']:02d}";folder.mkdir()
    for f in out.glob('scene-0*'):shutil.move(str(f),folder/f.name)
print('PASS campaign asset packages, area',area,flush=True)
