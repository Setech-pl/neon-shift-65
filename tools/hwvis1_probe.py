#!/usr/bin/env python3
"""Read-only standard OS SIO frame captures; uses private instrumented Atari800."""
import os,json,csv
from pathlib import Path
import release1_runtime as r
BASE=Path('build/hwvis1')
OBSERVER=(BASE/'observer/src/atari800').resolve()
def configure():
    r.BASE=BASE
    os.environ['NEON_RELEASE1_OBSERVER']=str(OBSERVER)
    native=r.setup
    def setup(b):
        labs=native(b)
        os.environ['HWVIS_ADDRS']=','.join(f'{labs.get(n,0):x}' for n in ('_native_dli','dli_row','_asset_loading','_phase','_native_vbi'))+',0'
        return labs
    r.setup=setup

def probe(build,name,events,captures,total,image=None):
    out,states,labs=r.probe(name,events,captures,total,build=Path(build),image=image,stock=True,raster=False)
    effective=json.loads((out/'hwvis-effective.json').read_text())
    assert effective==dict(machine_type=effective['XLXE_enum'],XLXE_enum=effective['XLXE_enum'],ram_kb=64,tv_lines=312,basic_disabled=1,sio_patch=0),effective
    return out,states,labs
if __name__=='__main__':
    import sys
    configure()
    events=[(3200,3200,dict(fire=0)),(4600,4600,dict(stick=7)),(4640,4640,dict(stick=7)),(4700,4700,dict(fire=0)),(5800,5800,dict(consol=6)),(5850,5850,dict(fire=0)),(5900,5900,dict(consol=6)),(5950,5950,dict(consol=6))]
    out,s,l=probe(sys.argv[1],sys.argv[2],events,list(range(1800,2751))+list(range(3200,4101))+list(range(4700,5401))+list(range(5780,6011)),6050)
    print(out, {f:s[f] for f in (2750,4100,5400,6010)})
