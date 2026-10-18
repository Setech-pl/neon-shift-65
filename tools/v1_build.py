#!/usr/bin/env python3
"""Build the frozen RELEASE1 candidate from the unchanged owner campaign."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True)
    p.add_argument('--pre-hwvis1',action='store_true',help='Reproduce historical RELEASE1 without HWVIS1 fixes')
    p.add_argument('--rc1',action='store_true',help='Reproduce the historical FINISH1 candidate')
    p.add_argument('--test-start',type=int,choices=(1,16,31,46),help='Hardware area test: full boot, auto-start, isolated save identity')
    p.add_argument('--band-colors-prototype',action='store_true',help='Diagnostic only: DLI shades crossing shared object/device colors; excluded from final')
    a=p.parse_args();os.chdir(ROOT)
    source=ROOT/'assets/levels/camp2-b/campaign.json';raw=source.read_bytes()
    levels=json.loads(raw)['levels'];assert len(levels)==60
    env=dict(os.environ,NEON_CAMPAIGN=str(source))
    if a.test_start and (a.rc1 or a.band_colors_prototype):p.error('test-start requires RC2')
    env['NEON_FINISH2']=str(int(not a.rc1 and not a.band_colors_prototype))
    env['NEON_FINISH2_START']=str(a.test_start or 0)
    env['NEON_HWVIS1']=str(int(not a.pre_hwvis1 and not a.rc1 and not a.band_colors_prototype))
    env['NEON_RELEASE1']=str(int(not a.rc1 and not a.band_colors_prototype))
    env.pop('NEON_CAMPAIGN_BOUNDS',None);env.pop('NEON_ART4',None)
    cmd=[sys.executable,'tools/product1_build.py','--campaign','--art-final','--out',a.out]
    if not a.band_colors_prototype:cmd.append('--finish1')
    if a.band_colors_prototype:cmd.append('--band-colors')
    subprocess.run(cmd,env=env,check=True)
    assert source.read_bytes()==raw,'Campaign changed during build'
    out=Path(a.out)
    binding=dict(source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(raw).hexdigest(),
                 authored_bounds='visual_size embedded in the unchanged source',levels=60,
                 art='Historical Energy bands diagnostic' if a.band_colors_prototype else 'FINISH1 RC1' if a.rc1 else 'RELEASE1 on FINISH2 RC2',band_colors=a.band_colors_prototype,
                 test_start=a.test_start,save_namespace='normal campaign' if not a.test_start else 'FINISH2 test '+str(a.test_start),
                 ATR_sha256=hashlib.sha256((out/'candidate.atr').read_bytes()).hexdigest(),
                 source_preserved=True,visual_owner='NOT_RUN')
    (out/'v1-binding.json').write_text(json.dumps(binding,indent=2)+'\n')


if __name__=='__main__':main()
