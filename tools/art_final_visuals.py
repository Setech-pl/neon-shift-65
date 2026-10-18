#!/usr/bin/env python3
"""Preserve native captures and compose integer-scale comparisons externally."""
import hashlib
import json
from pathlib import Path
import recovery1_visuals as visuals

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/art-final'
DEST=ROOT/'docs/art-final/screenshots'


def main():
    DEST.mkdir(parents=True,exist_ok=True);visuals.DEST=DEST;manifest=[]
    captures={name:json.loads((BASE/('captures-'+name+'.json')).read_text()) for name in ('before','bands','final')}
    levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels'];floor=[]
    for index,number in enumerate((1,5,9)):
        paths={}
        for variant in captures:
            r=captures[variant][index];source=ROOT/r['out']/f"native-{r['initial']:04}.png"
            paths[variant]=visuals.copy(source,f'energy-{number:02d}-{variant}',manifest)
            if variant=='final':
                source=ROOT/r['out']/f"native-{r['settled']:04}.png"
                visuals.copy(source,f'energy-{number:02d}-docked',manifest)
        visuals.pair(f'energy-{number:02d}-before-after',('RECOVERED VIS1-R2',paths['before']),('ART-FINAL ENERGY',paths['final']))
        visuals.pair(f'energy-{number:02d}-band-prototype',('ART-FINAL SELECTED',paths['final']),('BAND PROTOTYPE EXCLUDED',paths['bands']))
        # Initial empty floor cells only: exclude all goals and object cells.
        data={v:visuals.rgb(p) for v,p in paths.items()};values={v:[] for v in data};ink={v:0 for v in data}
        for y,row in enumerate(levels[number-1]['rows']):
            for x,ch in enumerate(row):
                if ch!=' ':continue
                for yy in range(64+16*y,80+16*y):
                    for xx in range(40+16*x,56+16*x):
                        for v,im in data.items():
                            r,g,b=im[yy][xx];values[v].append((2126*r+7152*g+722*b)/10000)
                            ink[v]+=im[yy][xx]!=im[0][0]
        floor.append(dict(number=number,pixels=len(values['before']),mean_RGB_luma={v:sum(a)/len(a) for v,a in values.items()},
                          non_background_pixels=ink,
                          method='Native PAL RGB weighted luma over authored initial empty floor tiles; all object/goal tiles excluded'))
    (ROOT/'docs/art-final/screenshots.json').write_text(json.dumps(dict(native=manifest,transform='Unmodified 336x240 native screenshots; 3x integer replication, labels outside frames',floor_measurements=floor),indent=2)+'\n')


if __name__=='__main__':main()
