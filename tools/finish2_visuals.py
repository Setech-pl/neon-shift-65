#!/usr/bin/env python3
"""Actual emulator PNGs; labels outside frames, integer comparison copies."""
import json
from pathlib import Path
import recovery1_visuals as v

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/finish2/screenshots'

def main():
    DEST.mkdir(exist_ok=True);v.DEST=DEST;manifest=[];records=[];paths={}
    for label,b in (('rc1',ROOT/'build/finish1/rc1'),('rc2',ROOT/'build/finish2/final')):
        run=b/'campaign-full';levels=json.loads((run/'campaign-result.json').read_text())['levels']
        for n in (1,2,9,16,24,31,39,46,54):
            r=levels[n-1];f=r['frame']-r['moves']*8-15
            paths[label,n]=v.copy(run/f'native-{f:04}.png',f'level-{n:02}-{label}',manifest)
            if label=='rc2':records.append(dict(level=n,frame=f))
        run=b/('finish2-before-patch' if label=='rc1' else 'presentation-patch')
        for name,f in (('menu',650),('loader',750)):
            paths[label,name]=v.copy(run/f'native-{f:04}.png',f'{name}-{label}',manifest)
    for n in (9,24,39,54):v.pair(f'level-{n:02}-before-after',('RC1',paths['rc1',n]),('RC2',paths['rc2',n]))
    for name in ('menu','loader'):v.pair(name+'-before-after',('RC1',paths['rc1',name]),('RC2',paths['rc2',name]))
    # One compact four-area comparison, unmodified native PNG content at2x.
    canvas=[];scale=2;width=336*scale;gap=16;header=28
    for n,area in ((9,'ENERGY'),(24,'HYDROPONIC'),(39,'DATA HUB'),(54,'REACTOR')):
        row=[[(16,24,32)]*(width*2+gap) for _ in range(240*scale+header)]
        for col,label in enumerate(('rc1','rc2')):
            im=v.rgb(paths[label,n]);left=col*(width+gap)
            for y,line in enumerate(im):
                pixels=[p for p in line for _ in range(scale)]
                for yy in range(scale):row[header+y*scale+yy][left:left+width]=pixels
            title=f'{area} {n:02} {label.upper()}'
            for i,ch in enumerate(title):
                for y,bits in enumerate(v.FONT.get(ch,'000000/000000/000000/000000/000000/000000/000000').split('/')):
                    for x,bit in enumerate(bits):
                        if bit=='1':
                            for dy in range(2):
                                for dx in range(2):row[6+y*2+dy][left+8+i*14+x*2+dx]=(230,235,240)
        canvas.extend(row)
    v.write_rgb(DEST/'four-areas-before-after-2x.png',canvas)
    r=ROOT/'build/finish2/final/energy02-stability'
    for f in (1246,1247,1266,1366):v.copy(r/f'native-{f:04}.png',f'energy02-stable-{f}',manifest)
    for n in (1,16,31,46):v.copy(ROOT/f'build/finish2/test-{n}/stock-area/native-2700.png',f'hardware-area-{n:02}-stock',manifest)
    (DEST.parent/'screenshots.json').write_text(json.dumps(dict(native=manifest,records=records,
        method='Unmodified native336x240 PNG; pair3x and grid2x integer replication, labels outside frame',
        source='Actual cold ATR emulator boots, same inputs/config/initial full campaign frames before/after'),indent=2)+'\n')

if __name__=='__main__':main()
