"""Route unchanged UX2 case and independent arithmetic/native contracts to v2.
Only output/root routing differs; all device events and validators retained.
"""
import sys,types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
a,mode,*args=sys.argv[1:];B=Path(f'build/eng3-observed-input-3pal/area-{a}')
S=R/'experiments/ux2-early-splash-and-loading-screen'
sys.path.insert(0,str(S));m=types.ModuleType('probe');m.__file__=str(S/'probe.py')
s=(S/'probe.py').read_text().replace("B=Path('build/ux2-early-splash-and-loading-screen')",f'B=Path({str(B)!r})').replace("'ux2-early-splash-and-loading-screen/'+name",f'{str(B.relative_to("build"))!r}+"/"+name')
exec(compile(s,str(S/'probe.py'),'exec'),m.__dict__);sys.modules['probe']=m
p=S/('ux2_runs.py' if mode=='case' else 'analyze_ux2.py')
s=p.read_text().replace("B=Path('build/ux2-early-splash-and-loading-screen')",f'B=Path({str(B)!r})')
sys.argv=[str(p)]+(['--one',*args] if mode=='case' else [])
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
