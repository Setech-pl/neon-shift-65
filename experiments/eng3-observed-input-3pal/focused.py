"""Preserved reviewer stimulus/oracles, routed to ENG2 and isolated outputs."""
from pathlib import Path
import os,sys,subprocess,shutil
from capture_cases import R,B,compress,js
a=sys.argv[1];review=R/'experiments/eng1-action-semantics-and-campaign-memory-review'
sys.path.insert(0,str(review));import analyze
target=B/'focused-final';target.mkdir(exist_ok=True);analyze.B=target
shutil.copyfile(R/'experiments/art3-contextual-decoration-review/palette-spec.json',target/'palette-spec.json')
os.environ['ART3_TARGET_BUILD']=str(B);os.environ['ART3_REVIEW_SLOT']='unused'
for script in ['order_repro_v3.py','phase_fixed_repro_v5.py','start_repro_v3.py','zr192_repro_v3.py']:
 p=review/script;t=p.read_text()
 t=t.replace("R/'build/eng1-action-semantics-and-campaign-memory-review'/os.environ.get('ART3_REVIEW_SLOT','candidate-v1')",repr(str(target)))
 # Keep B a Path, not a string after replacing its expression.
 t=t.replace('B='+repr(str(target)),'B=Path('+repr(str(target))+')')
 sys.argv=[str(p),a]
 exec(compile(t,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
 # Independent image/history routines complete before archiving.
 name={'order_repro_v3.py':'RZ200','phase_fixed_repro_v5.py':'undo311','start_repro_v3.py':'RS311','zr192_repro_v3.py':'ZR192'}[script]
 out=target/f'{name}-area-{a}';js(out/'adapter-provenance.json',dict(original=str(p.relative_to(R)),changes='Only output Path and target ENG2 build; unchanged waveform/oracle.'))
 compress(out)
