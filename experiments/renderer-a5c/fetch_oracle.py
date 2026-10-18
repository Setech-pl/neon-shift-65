"""Correct pre-origin snapshot with actual ANTIC bytes, never with PNG pixels.

Foreground early blank publication can occur after the observer's frame-origin
snapshot. Every fetched address must stay constant during the frame; corrected
RAM is independently checked against the entire native raster by legacy oracle.
"""
import csv,json,os
from pathlib import Path
import verify
def check(out,frames):
    out=Path(out);derive=out/'fetch-oracle';derive.mkdir(exist_ok=True)
    fetch={};counts={};conflicts=[]
    path=out/'antic-reads.csv'
    if path.exists():
        selected=set(frames)
        for row in csv.DictReader(path.open()):
            f=int(row['frame'])
            if f not in selected:continue
            key=int(row['address']);value=int(row['value']);values=fetch.setdefault(f,{})
            if key in values and values[key]!=value:conflicts.append(dict(frame=f,address=key,before=values[key],after=value,physical_line=int(row['ypos'])))
            values[key]=value;counts[f]=counts.get(f,0)+1
    assert not conflicts,conflicts[:8]
    corrected=[]
    for f,values in fetch.items():
        ram=bytearray((out/f'raster-{f:04}.ram').read_bytes());changes=[]
        for addr,v in values.items():
            if ram[addr]!=v:changes.append(dict(address=addr,before=ram[addr],fetched=v))
            ram[addr]=v
        (derive/f'raster-{f:04}.ram').write_bytes(ram)
        target=derive/f'native-{f:04}.png'
        if not target.exists():os.link(out/f'native-{f:04}.png',target)
        # Reactivation classification needs adjacent snapshot when available.
        prev=out/f'raster-{f-1:04}.ram';target_prev=derive/f'raster-{f-1:04}.ram'
        if prev.exists() and not target_prev.exists():target_prev.write_bytes(prev.read_bytes())
        corrected.append(dict(frame=f,read_count=counts[f],changes=changes))
    original=verify.pixel
    def pixel(path,f,lab):
        return verify.pixel_reference(derive if f in fetch else path,f,lab)
    verify.pixel=pixel
    try:r=verify.check(out,frames)
    finally:verify.pixel=original
    record=dict(status='PASS',actual_fetch_frames=len(fetch),reads=sum(counts.values()),stable_fetch_values=True,corrected=corrected,
      method='Only observed ANTIC screen/glyph read values replace pre-origin snapshot. Same frame must never fetch different values from same address; legacy full native pixel_reference compares independently. Mode2 glyph reads not instrumented, remain original snapshot; all corrections are mode4.')
    (out/'fetch-oracle.json').write_text(json.dumps(record,indent=2)+'\n')
    return r
