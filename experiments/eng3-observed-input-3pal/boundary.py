"""Run unchanged ART3 review stimulus/oracle against a named frozen build.
Only paths/slot routing differ. No timing, history, stimulus, thresholds changes.
"""
import os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
kind,area,slot,target=sys.argv[1:]
p=R/'experiments/art3-contextual-decoration-review'/({'order':'order_repro.py','undo':'phase_repro.py','start':'start_repro.py'}[kind])
sys.path.insert(0,str(p.parent))
os.environ['ART3_REVIEW_SLOT']=slot;os.environ['ART3_TARGET_BUILD']=target
s=p.read_text().replace("R/'build/art3-contextual-decoration-review'","R/'build/eng1-action-semantics-and-campaign-memory/boundaries'")
import analyze,shutil
analyze.B=R/'build/eng1-action-semantics-and-campaign-memory/boundaries'/slot
analyze.B.mkdir(parents=True,exist_ok=True)
shutil.copyfile(p.parent/'palette-spec.json',analyze.B/'palette-spec.json')
sys.argv=[str(p),area]
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
