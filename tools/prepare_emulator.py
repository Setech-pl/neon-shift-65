#!/usr/bin/env python3
"""Copy the available configured Atari800 source, add read-only frame capture.
Never changes the installed emulator or owner's source checkout.
"""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
source=Path(os.environ['NEON_ATARI_SOURCE']).resolve()
target=Path(os.environ.get('NEON_OBSERVER_OUT','.cache/observer')).resolve()
target.parent.mkdir(parents=True,exist_ok=True)
if not target.exists():shutil.copytree(source,target)
p=target/'src/cpu.c';s=p.read_text()
if 'NS65_Observe' not in s:
    s=s.replace('#include "voidstrike65_trace.h"','#include "voidstrike65_trace.h"\n#include "neon_trace.h"').replace('DFTrace_Observe(GET_PC(), A, X, Y, S);','DFTrace_Observe(GET_PC(), A, X, Y, S);\n        NS65_Observe(GET_PC(), S);')
    p.write_text(s)
s=p.read_text().replace('#include "voidstrike65_trace.h"','').replace('DFTrace_Observe(GET_PC(), A, X, Y, S);','')
p.write_text(s)
p=target/'src/atari.c';s=p.read_text()
if 'NS65_Frame' not in s:
    s=s.replace('void Atari800_Frame(void)','extern void NS65_Frame(void);\nvoid Atari800_Frame(void)').replace('Atari800_nframes++;','Atari800_nframes++;\n    NS65_Frame();')
    p.write_text(s)
s=p.read_text()
if 'NS65_BeforeRaster();' not in s:
    s=s.replace('extern void NS65_Frame(void);','extern void NS65_Frame(void);\nextern void NS65_BeforeRaster(void);').replace('ANTIC_Frame(TRUE);','NS65_BeforeRaster();\n\t\tANTIC_Frame(TRUE);')
    p.write_text(s)
shutil.copyfile('tools/emulator_trace.h',target/'src/neon_trace.h')
subprocess.run(['make','-C',str(target/'src'),'-j4'],check=True,stdout=subprocess.DEVNULL)
(target/'emulator-provenance.json').write_text(json.dumps(dict(source=str(source),copy=str(target),version='Atari800 7.1.2',patch_sha256=hashlib.sha256(Path('tools/emulator_trace.h').read_bytes()).hexdigest(),source_hashes={name:hashlib.sha256((source/'src'/name).read_bytes()).hexdigest() for name in ['cpu.c','atari.c','antic.c','screen.c']},binary_sha256=hashlib.sha256((target/'src/atari800').read_bytes()).hexdigest()),indent=2)+'\n')
print(target/'src/atari800')
