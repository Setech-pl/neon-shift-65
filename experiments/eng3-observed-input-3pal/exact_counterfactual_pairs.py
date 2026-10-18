"""Apply review correction to measurement search, preserving previous raw.

The neutral read at clock q permits an external transition at q because the
observer uses transition.clock < query.clock. An active read at q permits
transition q-1. The earlier search unnecessarily discarded both endpoints.
This tool is post-freeze report tooling; target sources and ATR stay frozen.
"""
from capture_cases import *
records=json.loads((D/'capture-128-final.json').read_text())['records'];updates=[]
for d in records:
 if d['opposite_pair']:continue
 q=d['job'];reverse=q[1][::-1];first='fire' if reverse[0]=='Z' else 'direction';second='direction' if first=='fire' else 'fire';bounds=d['edge_bounds_from_actual_device_queries']
 lo=max(bounds[first][0],bounds[second][0]-q[3]);hi=min(bounds[first][1],bounds[second][1]-q[3])
 if lo>hi:continue
 original=R/d['raw'];pq=[q[0]+'-opposite-exact217',reverse,(lo+hi+1)//2,q[3],q[4],q[5]]
 out=run(d['area'],'capture-exact-opposite',pq,d['external_events'][2][0]);od=json.loads((out/'result.json').read_text())
 samebus=(original/'device-reads.csv').read_bytes()==(out/'device-reads.csv').read_bytes();samecpu=transcript(original)==transcript(out);sameactions=d['actions']==od['actions']
 with tarfile.open(original/'raw.tar.gz') as t:images={str(f):t.extractfile(f'native-{f:04}.png').read()==(out/f'native-{f:04}.png').read_bytes() for f in range(1139,1149)}
 assert samebus and samecpu and sameactions and all(images.values())
 d['opposite_pair']=dict(raw=str(out.relative_to(R)),external_events=od['external_events'],gap=q[3],device_reads_identical=samebus,CPU_and_protocol_transcript_identical=samecpu,actual_actions_identical=sameactions,native_frames_identical=images,transcript_hash=transcript(out),review_search_correction=True)
 d['secondary']='C_EQUIVALENT_TRANSCRIPT_CURRENT_PATH';updates.append(dict(area=d['area'],id=d['id'],inclusive_search=[lo,hi],waveform=od['external_events']));compress(out)
same=sum(bool(d['opposite_pair']) for d in records)
js(D/'capture-128-qualified.json',dict(cases=128,same_217_clock_gap_pairs=same,only_different_1_clock_gap_pairs=128-same,review_correction=updates,records=records,earlier='capture-128-final.json preserves narrower search120/8; exact endpoint correction is a measurement change only.'))
print('exact search:',same,'same217;',128-same,'short gap only',updates)
