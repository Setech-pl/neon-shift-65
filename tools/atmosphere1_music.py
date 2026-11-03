"""Pack editable original 8x64-row scores into the existing NSRQ v2 player."""
import json,struct
from pathlib import Path
from warehouses import crc16
from atr import offset
ROOT=Path(__file__).resolve().parents[1]

def package(data):
    assert len(data)==1552
    h=bytearray(144);h[:8]=b'NSRQ'+bytes((2,5,1,0))
    struct.pack_into('<HH',h,8,len(data),crc16(data))
    struct.pack_into('<4H',h,16,0x1800,len(data),0,crc16(data))
    struct.pack_into('<H',h,12,crc16(h[16:]))
    struct.pack_into('<H',h,14,crc16(h[:14]))
    return bytes(h)+data

def scores():
    result=[]
    for name in ('hydroponic','data-hub','reactor'):
        p=ROOT/f'assets/audio/atmosphere1/{name}.json'
        j=json.loads(p.read_text())
        assert j['row_frames']==6 and len(j['patterns'])==8 and len(j['order'])==16
        assert all(0<=v<8 for v in j['order'])
        data=[]
        for pattern in j['patterns']:
            assert len(pattern)==64
            for row in pattern:
                assert len(row)==3 and all(type(x)==int and 0<=x<=255 for x in row) and row[2]<=3
                data.extend(row)
        result.append((name,bytes(data+j['order']),j['title']))
    return result

def pack(image,out):
    energy=(out/'music.nrq').read_bytes()
    assert len(energy)==1696
    manifest=[]
    for area,(name,raw,title) in enumerate([('energy',energy,'Service Current')]+[(n,package(b),t) for n,b,t in scores()],1):
        start=512+(area-1)*14
        image[offset(start,128):offset(start,128)+len(raw)]=raw
        (out/f'music-{area}.nrq').write_bytes(raw)
        manifest.append(dict(area=area,name=name,title=title,start_sector=start,bytes=len(raw),
                             source='tools/engine/compile.py:music' if area==1 else f'assets/audio/atmosphere1/{name}.json'))
    (out/'area-music.json').write_text(json.dumps(manifest,indent=2)+'\n')
