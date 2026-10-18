"""Separate untouched historical raw sequences from paired current failures."""
from pathlib import Path
import json,collections,hashlib
B=Path('build/eng3-observed-input-3pal');R=Path('build/eng3-observed-input-3pal-review');areas=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for a in range(1,5):
 old=Path(f'build/art2-four-area-themes/area-{a}/phase-accepted/ART2-comparison.json');raw=json.loads(old.read_text());counts=dict(collections.Counter(x['status'] for x in raw['results']))
 pair={}
 for slot in ['baseline-focused','candidate-v1']:
  pair[slot]={}
  for case in ['undo311','RZ200','RS311']:
   p=R/slot/f'{case}-area-{a}'/'independent-result.json';pair[slot][case]=dict(file=str(p),sha256=sha(p),result=json.loads(p.read_text()))
 areas.append(dict(area=a,historical_ART2_raw=counts,historical_source=str(old),historical_sha256=sha(old),paired=pair,classification='NEW ART3 boundary regression: undo image absent and requested RZ executed ZR' if a==3 else 'Inherited boundary failure: undo image absent and RZ executed ZR' if a==4 else 'No new failure in these bounded probes'))
trial={k:json.loads((R/'trial-area3-A'/f'{k}-area-3/independent-result.json').read_text()) for k in ['undo311','RZ200','RS311']}
d=dict(status='ENGINE_FAIL',qualification='FAIL_NEW_ART3_AREA3_BOUNDARY_REGRESSION',scope='Fresh paired3focused cases perarea plus area3 alternativeA. Not a new full142+45+106 sweep.',categories={'art':'Changed decoration pixels/slot IDs are expected. Palette remains ART2.1 exactly; static/dynamic actor shapes and ordered schedules unchanged. No candidate PNG is an oracle.','historical_raw':'Strict ART2 test compares10 robot frame indices, not RGB: areas1/3 raw106FAIL;2/4 raw105FAIL+1NOT_ACCEPTED. Historical106FAIL wording is imprecise, preserved unchanged.','action_acceptance':'A5c105PASS/1rawFAIL: A2 empty undo thenR versus A5cR thenundo; accepted sequence met actual-clock phase contract. Different accepted action/order is not a wrong glyph phase.','phase':'Fresh observed undo cases1/2 satisfy independent actual video-clock8active+2idle. Area3/4 haveNO_UNDO_IMAGE because emptyundo executes beforepush; this remainsFAIL, not a passed/omitted phase test. No newly demonstrated wrong phase of an accepted undo is claimed.','order':'Area3 changes ART2.1 RZ toART3 ZR. Area4alreadyZR inART2.1. Separatepush-beforeSTART and external first/full/HUD evidence lives in reviewer paired summary.'},areas=areas,trial_area3_A=trial,engine='FAIL',conclusion='Identical resident code does not establish unchanged boundary timing. Both planned decoration alternativesA/B reproduce newarea3 failure; no runtime/padding/CRC tuning made to conceal it.')
(B/'phase-classification.json').write_text(json.dumps(d,indent=2)+'\n');print('PASS historical preservation/classification; overall qualification andENGINE FAIL')
