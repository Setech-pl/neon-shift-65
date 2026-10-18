"""Per-area unchanged UX2 physical ATR fixtures and native raster oracle."""
import os,sys,runpy
from pathlib import Path
area=int(sys.argv[1]);fixture=sys.argv[2];mode=sys.argv[3]
B=Path(f'build/eng3-observed-input-3pal/area-{area}')/('open' if fixture=='open' else '')
os.environ['NEON_A5C_BUILD']=str(B)
base=Path('experiments/ux2-early-splash-and-loading-screen')
script={'game':'fixtures.py','dock':'dock_probe.py','measure':'measure_game.py','phase':'phase_test.py','phase-contract':'phase_contract.py','physical':'engine_physical.py','open-order':'open_regression.py'}[mode]
t=(base/script).read_text().replace("B=Path('build/ux2-early-splash-and-loading-screen')",f"B=Path({str(B)!r})")
t=t.replace("B=Path('build/ux2-early-splash-and-loading-screen/phase-accepted')",f"B=Path({str(B/'phase-accepted')!r})")
t=t.replace("g.ROOT=Path('build/ux2-early-splash-and-loading-screen')",f"g.ROOT=Path({str(B)!r})")
t=t.replace("'ux2-early-splash-and-loading-screen/game-accepted-dock'",repr(str(B.relative_to('build'))+'/game-accepted-dock'))
t=t.replace("'ux2-early-splash-and-loading-screen/phase-accepted/'",repr(str(B.relative_to('build'))+'/phase-accepted/'))
t=t.replace('own53-UX2','own53-ART2')
if fixture=='open' and script=='fixtures.py':
 # UX2's extra collision was UP against the new obstacle boundary. The old
 # open fixture has free floor above its initial player and a wall below.
 # Keep the C state oracle intact; use the actual DOWN wall for this check.
 t=t.replace("dict(stick=14))])","dict(stick=13))])")
if script=='phase_test.py':
 # Its recursive worker dispatch remains this wrapper with original context.
 t=t.replace("[sys.executable,__file__,'--one',v,k,str(p)]",f"[sys.executable,__file__,str({area}),{fixture!r},'phase','--one',v,k,str(p)]")
if script=='measure_game.py':
 # HUD expected colors are a frozen ART2.1 specification, never sampled pixels.
 t=t.replace(';import measure', ';import measure;import inspect;import json')
 spec=__import__('json').loads((Path(__file__).parent/'palette-oracle.json').read_text())['areas'][str(area)]
 t=t.replace('result={}', f"exec(inspect.getsource(measure.ratio_matches).replace('0xee', '{(spec['hud_pf2'] & 240) | 14}').replace('0xe0', '{spec['hud_pf2']}'), measure.__dict__)\nresult={{}}")
sys.argv=[__file__]+sys.argv[4:]
exec(compile(t,str(base/script),'exec'),{'__name__':'__main__','__file__':__file__})
