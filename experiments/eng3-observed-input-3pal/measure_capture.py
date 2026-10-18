"""Query intervals over an entire PAL raster, and observed capture spans.

Finite measurements are deliberately not relabelled all-path WCET.
"""
from capture_cases import *
import re,collections
PAL=35568;F=40511952
def labels(p):return {n:int(v,16) for v,n in re.findall(r'^al (\w+) \.(\w+)',p.read_text(),re.M)}
records=json.loads((D/'capture-128-final.json').read_text())['records'];metrics=[];groups=collections.defaultdict(list)
allspans=[]
for d in records:
 out=R/d['raw'];bus=rows(out/'device-reads.csv');lab=labels(B/f"area-{d['area']}"/(d['job'][5]+'.lbl'));coverage={}
 for addr in [0xd300,0xd010,0xd01f]:
  times=[r['clock'] for r in bus if r['address']==addr];intervals=[]
  for a,z in zip(times,times[1:]):
   lo=max(a,F+PAL);hi=min(z,F+2*PAL)
   if lo<hi:intervals.append(dict(first_query=a,next_query=z,clipped_begin=lo-(F+PAL),clipped_end=hi-(F+PAL),gap_clocks=z-a))
  assert sum(x['clipped_end']-x['clipped_begin'] for x in intervals)==PAL
  coverage[hex(addr)]=dict(frame=1141,covered_clocks=PAL,total_clocks=PAL,all312_lines=True,maximum_observed_query_gap=max(z-a for a,z in zip(times,times[1:])),intervals=intervals)
 with tarfile.open(out/'raw.tar.gz') as t:
  trace=[{k:int(v) for k,v in q.items()} for q in csv.DictReader(io.TextIOWrapper(t.extractfile('input-instructions.csv')))]
 previous=None;begin=None;defer=0;spans=[];readpcs=[]
 for r in trace:
  if previous and previous['opcode'] in (133,141) and previous['arg']&255==lab['_capture_active']:
   if previous['a']==1:begin=previous['clock'];defer=0
   elif previous['a']==0 and begin is not None:
    spans.append(dict(begin_lower=begin,end_upper=r['clock'],elapsed_upper=r['clock']-begin,deferred=defer));begin=None
  if r['opcode']==230 and r['arg']&255==lab['_deferred_epoch']:defer+=1
  previous=r
  if d['external_events'][0][0]-300<=r['clock']<=d['external_events'][1][0]+300:readpcs.append(r)
 # Classify the actual execution around the edge interval, using linker labels.
 near=[r for r in readpcs if d['external_events'][0][0]<=r['clock']<=d['external_events'][1][0]]
 if any(lab['_native_dli']<=r['pc']<=lab['_dli_end'] for r in near):cause='DLI_WSYNC_AND_CAPTURE_SERIALIZATION'
 elif any(lab['_native_vbi']<=r['pc']<=lab['_vbi_end'] for r in near) or any(r['pc']>=0xc000 for r in near):cause='VBI_OR_OS_SERVICE'
 elif any(lab['_input_wait']<=r['pc']<=lab['_input_wait']+150 for r in near):cause='SEQUENTIAL_IDLE_POLL_WITH_DMA'
 else:cause='FOREGROUND_WORK_BETWEEN_CAPTURE_QUERIES'
 groups[cause].append(dict(area=d['area'],id=d['id'],classification=d['classification'],secondary=d['secondary'],edge_instruction_brackets=near,read_bounds=d['edge_bounds_from_actual_device_queries']))
 metrics.append(dict(area=d['area'],id=d['id'],coverage=coverage,capture_count=len(spans),maximum_observed_lock_span=max(s['elapsed_upper'] for s in spans),maximum_deferred=max(s['deferred'] for s in spans),edge_execution_cause=cause,spans=spans))
 allspans.extend(spans)
js(D/'capture-intervals.json',dict(scope='128 freshly replayed mismatches. All intervals of frame1141 are bracketed by actual device queries in1140..1142. Full raster coverage for these executions, not every possible workload or waveform. Clocks are emulator device-query times.',cases=metrics,completed_lock_spans=len(allspans),maximum_observed_span=max(s['elapsed_upper'] for s in allspans),maximum_observed_deferred=max(s['deferred'] for s in allspans),all_path_WCET='UNRESOLVED',hardware_guarantee=False))
js(D/'capture-groups.json',dict(classification_counts={'B_CAPTURE_GAP':128,'C_current_path_equivalence':128,'A_demonstrated':0,'D_causing_the128':0},groups=dict(groups),limits='B denotes absence of a sufficient program acquisition during a physically readable interval. C is proved for this sampler transcript, not all possible standard65XE samplers. No ambiguity case is PASS. D latch-emulation defect is separate and unused by candidate.'))
print({k:len(v) for k,v in groups.items()},'max lock',max(s['elapsed_upper'] for s in allspans))
