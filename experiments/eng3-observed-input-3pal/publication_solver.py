"""Exhaustive zero-preparation necessary conditions for overlapping critical images.

Independent arithmetic model. This is a lower-bound feasibility rejection,
not a simulator or a constructive target scheduler. Every PAL clock is covered.
"""
from capture_cases import js,D
import math
PAL=312*114;gap=217;uncertainty=130
def sweep(height,advance_lines):
 first=185*114+43;last=first+(height-1)*114
 maximum=(-1,None);fails=0;segments=[];start=None
 for t0 in range(PAL):
  n=math.ceil((t0+1-first)/PAL) # transition equal-clock happens after read
  full1=n*PAL+last
  full2=(n+1)*PAL+last-advance_lines*114
  lower=full2-(t0+gap)-uncertainty
  bad=lower>2*PAL
  if bad:fails+=1
  if bad and start is None:start=t0
  if not bad and start is not None:segments.append([start,t0]);start=None
  if lower>maximum[0]:maximum=(lower,t0)
 if start is not None:segments.append([start,PAL])
 return dict(height=height,advance_lines=advance_lines,gap=gap,preparation=0,clock_phases_covered=PAL,maximum_lower_PAL=maximum[0]/PAL,worst_external_t0_phase=maximum[1],failed_clock_phases=fails,failing_intervals_half_open=segments,status='NECESSARY_CONDITION_FAIL' if fails else 'NECESSARY_ONLY_NOT_SUFFICIENT')
records=[sweep(h,k) for h in [16,32,48,64] for k in [0,48,64]]
js(D/'publication-solver.json',dict(PAL=PAL,scanline=114,scope='Overlapping critical pixels, distinct coherent images, fixed forward raster or ideal per-frame phase advance. Every312x114 clock phase enumerated. Zero CPU, arbitrary phase selection, no DLIST/commit/bank costs: optimistic necessary test only.',native_window_lines=240,preserved_ART3_HUD_and_playfield_lines=192,max_ideal_phase_range_lines=48,rows=records,limitations='64-line set is a conservative four-tile support model for consecutive vertical pushes; actual differing-pixel support and target five-bank geometry must be validated before treating it as universal product impossibility. Fixed raster rejection also has actual four-area ZR192 ANTIC witness, independent of this model.'))
print([(r['height'],r['advance_lines'],r['failed_clock_phases']) for r in records])
