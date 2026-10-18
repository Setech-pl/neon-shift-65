"""The physical contract has no minimum gap; supplement same-gap equivalence.

Keep the eight failed 217-clock counterfactual search results as raw evidence.
Do not label these as fixed-gap-equivalent. One-clock schedules are measurements,
not an approved new product requirement.
"""
from capture_cases import *
records=json.loads((D/'capture-128.json').read_text())['records']
for d in records:
 if d['opposite_pair']:continue
 a=d['area'];q=d['job'];reverse=q[1][::-1];first='fire' if reverse[0]=='Z' else 'direction';second='direction' if first=='fire' else 'fire';bounds=d['edge_bounds_from_actual_device_queries']
 gap=1;lo=max(bounds[first][0]+1,bounds[second][0]+1-gap);hi=min(bounds[first][1]-1,bounds[second][1]-1-gap)
 assert lo<=hi,('order distinguishable; do not relabel ambiguity',d)
 original=R/d['raw'];pq=[q[0]+'-opposite-gap1',reverse,(lo+hi)//2,gap,q[4],q[5]]
 out=run(a,'capture-short-opposite',pq,d['external_events'][2][0]);od=json.loads((out/'result.json').read_text())
 samebus=(original/'device-reads.csv').read_bytes()==(out/'device-reads.csv').read_bytes();samecpu=transcript(original)==transcript(out);sameactions=d['actions']==od['actions']
 with tarfile.open(original/'raw.tar.gz') as t:
  images={str(f):t.extractfile(f'native-{f:04}.png').read()==(out/f'native-{f:04}.png').read_bytes() for f in range(1139,1149)}
 assert samebus and samecpu and sameactions and all(images.values())
 d['supplemental_opposite_pair']=dict(raw=str(out.relative_to(R)),external_events=od['external_events'],gap=gap,original_gap=q[3],same_gap_equivalence=False,device_reads_identical=samebus,CPU_and_protocol_transcript_identical=samecpu,actual_actions_identical=sameactions,native_frames_identical=images,transcript_hash=transcript(out))
 d['secondary']='C_EQUIVALENT_TRANSCRIPT_CURRENT_PATH_DIFFERENT_GAP';compress(out);print(a,d['id'],'gap1 equivalent',flush=True)
js(D/'capture-128-final.json',dict(cases=128,same_217_clock_gap_pairs=sum(bool(d['opposite_pair']) for d in records),different_1_clock_gap_pairs=sum('supplemental_opposite_pair' in d for d in records),records=records))
