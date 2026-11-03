#!/usr/bin/env python3
"""Bounded PAL smoke on private disk copies; requires NS65 Atari800 observer."""
import argparse, os, sys, json, shutil, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import atmosphere1_verify as t
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--observer',type=Path,required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
b=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
os.environ.update(ENERGY_FIX1_OBSERVER=str(a.observer.resolve()),ENERGY_FIX1_CONFIG=str(a.config.resolve()))
t.BASE=out;(out/'normal-r2').symlink_to(b,target_is_directory=True);t.pixel=lambda *args:False
master=(b/'candidate.atr').read_bytes();digest=hashlib.sha256(master).hexdigest()
pin=lambda f,**kw:(f,f,kw)
results=[]
def probe(name,events,frames,total,image=None):
 r,ss,l=t.probe(name,'normal',events,frames,total,image=image)
 results.append(dict(case=name,states=ss,timing=json.loads((r/'timing.json').read_text()),effective=json.loads((r/'hwvis-effective.json').read_text())))
 return r,ss,l
def capture(r,f,name):shutil.copyfile(r/f'native-{f:04}.png',out/(name+'.png'))
# Normal menu -> selector -> explicit confirmation -> each area's first room.
for n in (1,16,31,46):
 ev=[pin(3200,stick=14),pin(3250,fire=0),pin(4200,fire=0),pin(4300,fire=0),pin(4500,fire=0),pin(4600,stick=7),pin(4700,fire=0)]
 r,ss,l=probe(f'area-{n:02}',ev,[3000,4000,4650,7000],7020,t.save_image(master,n))
 assert ss[3000]['phase']==0 and ss[4000]['phase']==12
 s=ss[7000];assert s['scene']==n-1 and s['phase']==1 and s['loaded']==s['pmg_active']==1 and s['moves']==s['pushes']==s['undo']==0,s
 assert (r/'play.atr').read_bytes()==t.save_image(master,n)
 capture(r,7000,f'area-{n:02}')
 if n==1:capture(r,3000,'menu');capture(r,4000,'selector')
# Movement, push, undo; options toggles; resume preserves board and history.
ev=[pin(3200,fire=0)]+[pin(4550+40*i,stick=t.STICK[c]) for i,c in enumerate('UDRR')]
ev += [pin(4850,consol=5),pin(5100,consol=3),pin(6000,fire=0),pin(6100,stick=13),pin(6200,fire=0),pin(6300,stick=13),pin(6400,fire=0)]
# START pause, SELECT save, then cold loader Continue.
ev += [pin(7800,consol=6),pin(8000,consol=5),pin(10400,stick=13),pin(10500,fire=0)]
r,ss,l=probe('actions-save',ev,[4500,4800,5000,5600,6250,7500,7900,10000,13000],13020,t.save_image(master,1))
assert ss[4800]['moves']>0 and ss[4800]['pushes']>0
assert ss[5000]['moves']==ss[4800]['moves']-1 and ss[5000]['undo']==ss[4800]['undo']-1
for key in ('player','boxes','moves','pushes','undo'):assert ss[5000][key]==ss[7500][key],key
assert ss[5600]['phase']==12 and not ss[6250]['music_enabled'] and not ss[6250]['sfx_enabled']
assert ss[7500]['phase']==1 and ss[7900]['phase']==3 and ss[10000]['phase']==0
assert ss[13000]['phase']==1 and ss[13000]['undo']==ss[7500]['undo']
for key in ('player','boxes','moves','pushes'):assert ss[13000][key]==ss[7500][key],key
saved=(r/'play.atr').read_bytes();span=t.save_span(saved)
assert saved!=t.save_image(master,1) and saved[:span.start]+saved[span.stop:]==master[:span.start]+master[span.stop:]
capture(r,5600,'options')
# New emulator process proves disk persistence, independent of prior RAM.
r,ss,l=probe('cold-continue',[pin(3150,stick=13),pin(3200,fire=0)],[4500],4520,saved)
for key in ('player','boxes','moves','pushes'):assert ss[4500][key]==results[-2]['states'][13000][key],key
assert ss[4500]['undo']==0 and (b/'candidate.atr').read_bytes()==master
(out/'result.json').write_text(json.dumps(dict(status='PASS',master_sha256=digest,records=results),indent=2)+'\n')
# Keep sparse summaries + seven screenshots, discard observer transient evidence.
for r in (out/'runs').iterdir():
 for f in r.iterdir():
  if f.name not in ('summary.json','timing.json','hwvis-effective.json','emulator.log'):f.unlink()
print('PASS menu, selector, four areas, options/resume, move/push/undo, save and cold Continue')
