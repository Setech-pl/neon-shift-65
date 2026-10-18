"""Unchanged independent ART3 patterned-walk and immutable floor oracle, v2."""
from pathlib import Path
import sys,os
R=Path(__file__).resolve().parents[2];S=R/'experiments/art3-contextual-decoration-review';sys.path.insert(0,str(S))
a,f=sys.argv[1:];p=S/'floor_walk.py'
s=p.read_text().replace('build/art3-contextual-decoration/area-','build/eng3-observed-input-3pal/area-').replace("R/'build/art3-contextual-decoration-review'","R/'build/eng3-observed-input-3pal/floors'")
os.environ['ART3_REVIEW_SLOT']='final';sys.argv=[str(p),a,f]
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
from floor_restore import one
root=R/'build/eng3-observed-input-3pal/floors/final/floor-walk'
r=one(root,int(a),f,R/'experiments/eng3-observed-input-3pal');(root/f'area-{a}-{f}/floor-result.json').write_text(__import__('json').dumps(r,indent=2)+'\n')
