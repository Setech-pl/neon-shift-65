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
    p.add_argument('--pmg1',action='store_true',help='Isolated PMG1 prototype; never writes dist')
    p.add_argument('--pmg-industrial1',action='store_true',help='Industrial reference artwork with the PMG1 robot, outside dist')
    p.add_argument('--final-fix1',action='store_true',help='Atomic display reveal and deferred auto-save presentation')
    p.add_argument('--neon-areas1',action='store_true',help='Four industrial areas, shared data-driven PMG neon')
    p.add_argument('--energy-neon1',action='store_true',help='Energy cyan PMG installation and travelling cable light')
    p.add_argument('--energy-fix1',action='store_true',help='FINAL1 with bounded local instrument ambient and protected delivery')
    p.add_argument('--energy-final1',action='store_true',help='Final Energy metal and yellow service accents')
    p.add_argument('--energy-detail1',action='store_true',help='Energy-only offline panel and equipment revision on PMG-INDUSTRIAL1')
    p.add_argument('--pre-hwvis1',action='store_true',help='Reproduce historical RELEASE1 without HWVIS1 fixes')
    p.add_argument('--rc1',action='store_true',help='Reproduce the historical FINISH1 candidate')
    p.add_argument('--test-start',type=int,choices=(1,3,16,31,46),help='Hardware area test: full boot, auto-start, isolated save identity')
    p.add_argument('--band-colors-prototype',action='store_true',help='Diagnostic only: DLI shades crossing shared object/device colors; excluded from final')
    a=p.parse_args();os.chdir(ROOT)
    if a.final_fix1:a.neon_areas1=True
    if a.neon_areas1:a.energy_neon1=True
    if a.energy_neon1:a.energy_fix1=True
    if a.energy_fix1:a.energy_final1=True
    if a.test_start==3 and not a.energy_final1:p.error("test-start 3 is isolated to ENERGY-FINAL1")
    if a.energy_final1:a.energy_detail1=True
    if a.energy_detail1:a.pmg_industrial1=True
    if a.pmg_industrial1:a.pmg1=True
    if a.pmg1:
        if a.rc1 or a.pre_hwvis1 or a.band_colors_prototype:p.error('--pmg1 requires current HWVIS1')
        if (ROOT/'dist').resolve() in Path(a.out).resolve().parents or Path(a.out).resolve()==(ROOT/'dist').resolve():p.error('PMG1 output must remain outside dist')
    source=ROOT/'assets/levels/camp2-b/campaign.json';raw=source.read_bytes()
    levels=json.loads(raw)['levels'];assert len(levels)==60
    env=dict(os.environ,NEON_CAMPAIGN=str(source))
    env['NEON_PMG1']=str(int(a.pmg1))
    env['NEON_PMG_INDUSTRIAL1']=str(int(a.pmg_industrial1))
    env['NEON_FINAL_FIX1']=str(int(a.final_fix1))
    env['NEON_AREAS1']=str(int(a.neon_areas1))
    env['NEON_ENERGY_NEON1']=str(int(a.energy_neon1))
    env['NEON_ENERGY_FIX1']=str(int(a.energy_fix1))
    env['NEON_ENERGY_FINAL1']=str(int(a.energy_final1))
    env['NEON_ENERGY_DETAIL1']=str(int(a.energy_detail1))
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
                 art='NEON-AREAS1 on ENERGY-NEON1' if a.neon_areas1 else 'ENERGY-NEON1 on ENERGY-FIX1' if a.energy_neon1 else 'ENERGY-FIX1 on ENERGY-FINAL1' if a.energy_fix1 else 'ENERGY-FINAL1' if a.energy_final1 else 'ENERGY-DETAIL1 on PMG-INDUSTRIAL1' if a.energy_detail1 else 'PMG-INDUSTRIAL1 on PMG1/HWVIS1' if a.pmg_industrial1 else 'PMG1 prototype on HWVIS1' if a.pmg1 else 'Historical Energy bands diagnostic' if a.band_colors_prototype else 'FINISH1 RC1' if a.rc1 else 'RELEASE1 on FINISH2 RC2',band_colors=a.band_colors_prototype,
                 test_start=a.test_start,save_namespace='normal campaign' if not a.test_start else 'FINISH2 test '+str(a.test_start),
                 ATR_sha256=hashlib.sha256((out/'candidate.atr').read_bytes()).hexdigest(),
                 source_preserved=True,visual_owner='NOT_RUN')
    (out/'v1-binding.json').write_text(json.dumps(binding,indent=2)+'\n')


if __name__=='__main__':main()
