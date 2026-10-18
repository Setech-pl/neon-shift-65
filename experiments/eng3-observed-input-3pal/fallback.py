"""Read-only capture measurement under one deliberately missing DLI frame."""
from pathlib import Path
import os,sys,json,csv
sys.path.insert(0,'experiments/renderer-a5c');sys.path.insert(0,'tools')
import gauntlet,verify,turbo_run
from emulator_smoke import run as native
from observed_oracle import transactions,runtime_read_pcs
area=int(sys.argv[1]);B=Path(f'build/eng3-observed-input-3pal/area-{area}');out=B/'missing-dli'
analyze='--analyze-only' in sys.argv
if not analyze:assert not out.exists();out.mkdir()
os.environ.update(NEON_A5B_OBSERVER=str(Path('build/eng3-observed-input-3pal/observer-missing-dli/src/atari800').resolve()),ENG3_MISSING_DLI='1140,1140',ENG2_BUS_RANGE='1139,1142')
gauntlet.ROOT=B
def run(n,*a,**kw):kw['boot']=True;return native(str(out.relative_to('build')),*a,**kw)
gauntlet.run=run
if not analyze:gauntlet.probe('missing-dli',[(700,700,dict(fire=0)),(1140,1140,dict(stick=7))],list(range(1139,1144)),1148,variant='carry',boot=True)
bus=[{k:int(v) for k,v in r.items()} for r in csv.DictReader((out/'device-reads.csv').open())]
pcs=runtime_read_pcs(B/'carry.xex')
# A clipped log can start in the preceding probe. Keep that partial explicitly,
# then parse only complete fixed-protocol transactions (no outcome selection).
begin=next(i for i,q in enumerate(bus) if q['pc'] in pcs and q['address']==0xd300)
obs,meta=transactions(bus[begin:],pcs);meta['leading_clipped_queries']=bus[:begin]
# ISR input_sample has literal device-read instructions in this bounded routine.
l=verify.labels(B/'carry.lbl');sample=l['input_sample'];fallback=[o for o in obs if o['frame']==1140 and sample<=o['queries'][0]['pc']<sample+150 and o['queries'][0]['clock']%35568>200*114]
assert fallback,(area,'missing-DLI VBI fallback absent')
r=dict(area=area,status='CAPTURE_FALLBACK_PASS',scope='Diagnostic host hardware fault suppresses all DLI NMIs in PAL1140; VBI and candidate bytes unchanged. Palette/bank scanout in the fault frame is not claimed ART3 PASS.',fallback=fallback,observations=obs,capture=meta,artifact=json.loads((out/'artifact.json').read_text()))
(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(area,'VBI fallback captured',len(fallback))
