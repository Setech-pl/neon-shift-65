#!/usr/bin/env python3
"""Validate authored warehouse pixels and build versioned scene packages."""
import hashlib,json,struct
from pathlib import Path
from assets import pixels,encode_tile,decode_tile,png

def crc16(data):
    c=0xffff
    for v in data:
        c ^= v<<8
        for _ in range(8):c=((c<<1)^0x1021 if c&0x8000 else c<<1)&0xffff
    return c

def compile_sets():
    spec=json.loads(Path('assets/graphics/warehouses.json').read_text())
    levels=json.loads(Path('assets/levels/prototypes.json').read_text())['levels']
    assert spec['version']==1 and [t['id'] for t in spec['sets']]==[1,2]
    out=Path('build/warehouses');out.mkdir(exist_ok=True)
    result=[]
    for theme in spec['sets']:
        tiles=theme['walls']+[theme['docked']]+theme['floors']+[theme['module']]
        assert [t['base'] for t in tiles]==list(range(4,80,4))+[84]
        patch=bytearray();atlas=[]
        for t in tiles:
            p=pixels(t['rows'],8,16);data=bytes(encode_tile(p))
            assert decode_tile(data)==p
            patch+=data;atlas.append(p)
        assert len(patch)==640 and all(0<=v<14 for v in theme['neighbor_lut'])
        assert len(theme['neighbor_lut'])==16
        overrides=bytearray()
        assert len(theme['overrides'])<=16
        seen=set()
        for level,x,y,tile in theme['overrides']:
            assert 0<=level<3 and 0<=tile<14
            assert levels[level]['rows'][y][x]=='#'
            assert (level,x,y) not in seen;seen.add((level,x,y))
            overrides+=bytes([level,x,y,4+tile*4])
        overrides+=bytes([255,0,0,0])*(16-len(overrides)//4)
        a=theme['animation'];assert a['base']==56 and 16<=a['period']<=255
        assert len(a['frames'])==2 and a['frames'][0]==theme['walls'][13]['rows']
        anim=bytes(v for rows in a['frames'] for v in encode_tile(pixels(rows,8,16)))
        body=bytes(patch)+bytes(4+v*4 for v in theme['neighbor_lut'])+overrides+anim
        assert len(body)==784
        # Header 32B: NSWP, version, codec RAW, id, image id, stored/raw,
        # body CRC16, palette5, anim base/period/count, music id, contract,
        # header CRC16. All words little endian. Reserved bytes are zero.
        header=bytearray(32);header[:4]=b'NSWP';header[4:6]=bytes([1,0])
        struct.pack_into('<HHHHH',header,6,theme['id'],1,len(body),len(body),crc16(body))
        header[16:21]=bytes(theme['palette'])
        assert header[16]==0 and header[20]==10 and all(v%2==0 for v in header[16:21])
        header[21:24]=bytes([a['base'],a['period'],2])
        struct.pack_into('<HH',header,24,theme['future_music_id'],1)
        struct.pack_into('<H',header,30,crc16(header[:30]))
        package=bytes(header)+body;(out/f'scene-{theme["id"]}.nwp').write_bytes(package)
        rows=[[0]*80 for _ in range(64)]
        for i,p in enumerate(atlas):
            for y,r in enumerate(p):rows[i//10*16+y][i%10*8:i%10*8+8]=r
        pal=json.loads(Path('assets/graphics/pal-palette.json').read_text())['rgb']
        colors=[pal[v] for v in theme['palette'][:4]]
        png(out/f'atlas-{theme["id"]}.png',rows,colors,scale_x=4)
        result.append(dict(id=theme['id'],name=theme['name'],bytes=len(package),raw=len(body),
                           sha256=hashlib.sha256(package).hexdigest(),crc16=crc16(body)))
    (out/'report.json').write_text(json.dumps(dict(status='PASS',packages=result),indent=2)+'\n')
    return result

if __name__=='__main__':
    print('PASS warehouse assets',compile_sets())
