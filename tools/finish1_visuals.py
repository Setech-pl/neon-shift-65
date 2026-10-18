#!/usr/bin/env python3
"""Actual same-frame PAL comparisons, labels outside unchanged native frames."""
import json
from pathlib import Path
import recovery1_visuals as v

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/finish1/screenshots'

def main():
    DEST.mkdir(parents=True,exist_ok=True);v.DEST=DEST;manifest=[];records=[];paths={}
    for name,build in (('before',ROOT/'build/art-final/final'),('rc1',ROOT/'build/finish1/rc1')):
        levels=json.loads((build/'campaign-full/campaign-result.json').read_text())['levels']
        for number in (1,5,9,24,39,54):
            r=levels[number-1];f=r['frame']-r['moves']*8-15
            paths[name,number]=v.copy(build/f'campaign-full/native-{f:04}.png',f'level-{number:02d}-{name}',manifest)
            if name=='rc1':
                v.copy(build/f"campaign-full/native-{r['frame']:04}.png",f'level-{number:02d}-solved',manifest)
                records.append(dict(level=number,initial_frame=f,solved_frame=r['frame']))
    canvas=[];scale=2;gap=16;header=28;width=336*scale
    for number,area in ((9,'ENERGY'),(24,'HYDROPONIC'),(39,'DATA HUB'),(54,'REACTOR')):
        v.pair(f'level-{number:02d}-before-after',(area+' F5DF646',paths['before',number]),(area+' V1.0-RC1',paths['rc1',number]))
        row=[[(16,24,32)]*(width*2+gap) for _ in range(240*scale+header)]
        for column,(label,key) in enumerate(((f'{area} {number:02d} - F5DF646','before'),(f'{area} {number:02d} - V1.0-RC1','rc1'))):
            im=v.rgb(paths[key,number]);left=column*(width+gap)
            for y,line in enumerate(im):
                pixels=[p for p in line for _ in range(scale)]
                for yy in range(scale):row[header+y*scale+yy][left:left+width]=pixels
            for i,ch in enumerate(label):
                for y,bits in enumerate(v.FONT.get(ch,'000000/000000/000000/000000/000000/000000/000000').split('/')):
                    for x,bit in enumerate(bits):
                        if bit=='1':
                            for dy in range(2):
                                for dx in range(2):row[6+y*2+dy][left+8+i*14+x*2+dx]=(230,235,240)
        canvas.extend(row)
    v.write_rgb(DEST/'four-areas-before-after-2x.png',canvas)
    (ROOT/'docs/finish1/screenshots.json').write_text(json.dumps(dict(native=manifest,records=records,
        transform='Unmodified native 336x240 screenshots; combined image 2x and pairs 3x integer replication, labels outside frames',
        source='Actual cold ATR boots and full60 replays; exact same PAL frame, config, input and logical game states verified separately'),indent=2)+'\n')
    print('PASS native copies and combined four-area before/after')

if __name__=='__main__':main()
