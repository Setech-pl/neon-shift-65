#!/usr/bin/env python3
"""Bootable raw-sector ATR; all sector/directory addresses are uint16.
Geometry math includes the three short boot sectors on 256B ATRs.
The production boot/SIO path currently validates 128B geometry only.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from warehouses import compile_sets,crc16

def offset(sector,sector_bytes):
    assert 1<=sector<=65535 and sector_bytes in (128,256)
    return 16+(sector-1)*128 if sector<=3 else 16+384+(sector-4)*sector_bytes

def empty_atr(sectors,sector_bytes):
    assert 3<=sectors<=65535 and sector_bytes in (128,256)
    size=384+(sectors-3)*sector_bytes;paragraphs=size//16
    assert paragraphs<=0xffffffff
    h=bytearray(16);struct.pack_into('<HHH',h,0,0x296,paragraphs&65535,sector_bytes)
    struct.pack_into('<H',h,6,paragraphs>>16) # byte7 remains0 for all supported geometries
    return h+bytearray(size)

def chunks(xex):
    assert xex[:2]==b'\xff\xff';p=2;out=[];run=None
    while p<len(xex):
        if xex[p:p+2]==b'\xff\xff':p+=2;continue
        start,end=struct.unpack_from('<HH',xex,p);p+=4;n=end-start+1
        assert n>0 and p+n<=len(xex);data=xex[p:p+n];p+=n
        if start==0x2e00:continue # cc65 transient SYSCHK; explicit PAL64 boot contract
        if start==0x2e2:continue  # INITAD points to the skipped SYSCHK
        if start==0x2e0:run=struct.unpack('<H',data)[0];continue
        assert not (start<0xbc20 and end>=0xb800), 'boot workspace collision'
        out.append((start,data))
    assert run is not None
    return out,run

def build(config=None,xex='build/neon-shift-65.xex',output='build/neon-shift-65.atr'):
    c=config or json.loads(Path('cfg/disk.json').read_text());b=c['sector_bytes'];sectors=c['sectors']
    assert c['version']==1 and b==128, 'runtime boot/loader currently supports 128B sectors'
    assert c['image_id']==1 and len(c['scene_starts'])==2
    packages=compile_sets();image=empty_atr(sectors,b);used={1,2,3,4}
    boot=Path('build/warehouse-boot.bin').read_bytes();assert len(boot)==384
    image[16:400]=boot
    records,entry=chunks(Path(xex).read_bytes())
    stream=b''.join(struct.pack('<HH',addr,len(data))+data for addr,data in records)+struct.pack('<HH',entry,0)
    n=(len(stream)+b-1)//b;assert 5+n<=min(c['scene_starts']), 'program/package collision'
    image[offset(5,b):offset(5,b)+len(stream)]=stream;used.update(range(5,5+n))
    directory=bytearray(128);directory[:4]=b'NSWD';directory[4:6]=bytes([1,2])
    struct.pack_into('<H',directory,6,c['image_id'])
    for k,pkg in enumerate(packages):
        data=Path(f'build/warehouses/scene-{pkg["id"]}.nwp').read_bytes()
        start=c['scene_starts'][k];count=(len(data)+b-1)//b
        assert start>=5 and start+count-1<=sectors
        assert not used.intersection(range(start,start+count)), 'sector overlap'
        used.update(range(start,start+count))
        image[offset(start,b):offset(start,b)+len(data)]=data
        struct.pack_into('<8H',directory,32+k*16,pkg['id'],c['image_id'],start,count,len(data),pkg['raw'],pkg['crc16'],0)
        pkg.update(start=start,last=start+count-1,sectors=count,read_bytes=count*b)
    struct.pack_into('<H',directory,126,crc16(directory[:126]))
    image[offset(4,b):offset(4,b)+128]=directory
    free=(sectors-len(used))*b;assert free>=c['future_reserve_bytes']
    Path(output).write_bytes(image)
    report=dict(status='PASS',artifact=output,sha256=hashlib.sha256(image).hexdigest(),
                atr_bytes=len(image),sector_bytes=b,sectors=sectors,data_bytes=len(image)-16,
                usable_after_boot_catalog=(sectors-4)*b,allocated_sectors=len(used),
                allocated_bytes=len(used)*b,free_bytes=free,reserve_bytes=c['future_reserve_bytes'],
                program_stream_bytes=len(stream),program_sectors=n,entry=entry,
                packages=packages,header_hex=image[:16].hex(),
                format='raw sectors; no DOS sector chains or VTOC',address_bits=16)
    Path(output).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sectors',type=int);p.add_argument('--output',default='build/neon-shift-65.atr')
    a=p.parse_args();c=json.loads(Path('cfg/disk.json').read_text())
    if a.sectors:c['sectors']=a.sectors
    print(json.dumps(build(c,output=a.output),indent=2))
