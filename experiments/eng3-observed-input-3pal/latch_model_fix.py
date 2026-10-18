"""Correct independently reproduced D-class defect in a NEW host observer.

Final candidate never enables the latch. The qualification observer and old raw
remain unchanged; this fix only permits future latch-enabled measurements.
"""
from capture_cases import *
import shutil,struct
O=B/'observer-latch-corrected-v4';assert not O.exists();RUN='fully-qualified-'
shutil.copytree(B/'observer',O)
p=O/'src/neon_trace.h';t=p.read_text();old='GTIA_TRIG[0]=fire&1;B5_SetConsole(console);'
assert t.count(old)==1
t=t.replace(old,'GTIA_TRIG[0]=fire&1;if(GTIA_GRACTL&4)GTIA_TRIG_latch[0]&=GTIA_TRIG[0];B5_SetConsole(console);');p.write_text(t)
t=t.replace('active=1;stick=ss[next];fire=ff[next];console=cc[next];','active=1;stick=ss[next];fire=ff[next];console=cc[next];if(GTIA_GRACTL&4)GTIA_TRIG_latch[0]&=fire&1;');p.write_text(t)
# Process pending edges under the OLD GRACTL before applying its write.
gtia=O/'src/gtia.c';g=gtia.read_text();sig='void GTIA_PutByte(UWORD addr, UBYTE byte)\n{';assert sig in g
g=g.replace(sig,sig+'\n extern void ENG2_Control(UWORD addr,UBYTE byte);\n B5_Pins();\n ENG2_Control(addr,byte);')
assert g.count('GTIA_GRACTL = byte;')==1
g=g.replace('GTIA_GRACTL = byte;','GTIA_GRACTL = byte;\n if(byte&4){int i;for(i=0;i<4;i++)GTIA_TRIG_latch[i]&=GTIA_TRIG[i];}')
gtia.write_text(g)
with p.open('a') as f:f.write('''
void ENG2_Control(UWORD addr,UBYTE byte)
{
 static FILE *f;
 if(addr!=0xd01d || !ns65_dir)return;
 if(!f){char path[1024];snprintf(path,sizeof(path),"%s/control-writes.csv",ns65_dir);f=fopen(path,"w");if(f)fprintf(f,"clock,address,value\\n");}
 if(f)fprintf(f,"%llu,%u,%u\\n",(unsigned long long)ANTIC_CPU_CLOCK,addr,byte);
}
''')
# Touch only cpu.c: make -B also invokes unavailable maintainer autotools.
cpu=O/'src/cpu.c';cpu.write_text(cpu.read_text())
with (B/'latch-model-build.log').open('w') as f:
 subprocess.run(['make','-C',str(O/'src'),'-j3'],stdout=f,stderr=subprocess.STDOUT,check=True)
def micro(name,code,pins):
 out=B/(RUN+name);out.mkdir()
 (out/'probe.xex').write_bytes(struct.pack('<HHH',0xffff,0x2000,0x2000+len(code)-1)+code+struct.pack('<HHH',0x2e0,0x2e1,0x2000))
 (out/'pins.csv').write_text(''.join(','.join(map(str,q))+'\n' for q in pins))
 cfg=R/'docs/audit/evidence-2026-10-08-160947/runtime-pal-final/emulator.cfg';(out/'emulator.cfg').write_text(cfg.read_text().replace('SOUND_ENABLED=1','SOUND_ENABLED=0'))
 argv=[str(O/'src/atari800'),'-config',str(out/'emulator.cfg'),'-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-nortime','-turbo','-windowed','-run',str(out/'probe.xex')]
 env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NS65_OUTPUT=str(out),NS65_CAPTURE='100,113,114,140',NS65_LIMIT='145',NSQ_PIN_SCHEDULE=str(out/'pins.csv'),UX1_REGISTER_LOG=str(out/'register-writes.csv'))
 with (out/'emulator.log').open('w') as f:subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
 samples=[]
 for frame in [100,113,114,140]:
  ram=(out/f'frame-{frame:04}.ram').read_bytes();samples.append(dict(frame=frame,startup_marker=ram[0x3002],reset_marker=ram[0x3003],TRIG0=ram[0x3001]))
 js(out/'result.json',dict(samples=samples,external_events=pins,target_sha256=sha(out/'probe.xex')))
 return samples,out
retcode=bytes.fromhex('78 a9 00 8d 0e d4 a9 04 8d 1d d0 a9 00 8d 00 30 a9 a5 8d 02 30 ad 10 d0 8d 01 30 d0 03 ee 00 30 4c 15 20')
ret,_=micro('latch-retention-corrected',retcode,[(4000200,15,0,7),(4000400,15,1,7)])
assert ret[0]['startup_marker']==0xa5 and all(q['TRIG0']==0 for q in ret[1:])
shortcode=bytes.fromhex('78 a9 00 8d 0e d4 a9 04 8d 1d d0 a9 a5 8d 02 30 a9 00 8d 0a d4 ad 10 d0 8d 01 30 4c 10 20')
short,so=micro('latch-pulse-during-WSYNC',shortcode,[(4000200,15,0,7),(4000201,15,1,7)])
events=rows(so/'fixed-pin-events.csv');assert events[0]['first_evaluation_clock']==events[1]['first_evaluation_clock']
assert all(q['TRIG0']==0 for q in short[1:]),short
out=B/(RUN+'latch-reset-repress');out.mkdir()
code=bytearray.fromhex('78 a9 00 8d 0e d4 a9 04 8d 1d d0 a9 a5 8d 02 30')
def loopwait(addr,cmp,branch):
 code.extend([0xad,addr&255,addr>>8,0xc9,cmp,branch,0xf9])
loopwait(0xd010,0,0xd0);loopwait(0xd40b,124,0x90)
code.extend(bytes.fromhex('a9 00 8d 1d d0 a9 04 8d 1d d0 a9 a6 8d 03 30'))
loop=0x2000+len(code);code.extend([0xad,0x10,0xd0,0x8d,1,0x30,0x4c,loop&255,loop>>8])
(out/'probe.xex').write_bytes(struct.pack('<HHH',0xffff,0x2000,0x2000+len(code)-1)+code+struct.pack('<HHH',0x2e0,0x2e1,0x2000))
pins=[(4000200,15,0,7),(4000400,15,1,7),(4025000,15,0,7),(4025200,15,1,7)]
(out/'pins.csv').write_text(''.join(','.join(map(str,q))+'\n' for q in pins));shutil.copyfile(B/(RUN+'latch-retention-corrected')/'emulator.cfg',out/'emulator.cfg')
argv=[str(O/'src/atari800'),'-config',str(out/'emulator.cfg'),'-no-autosave-config','-xl','-pal','-nobasic','-no-mapram','-nostereo','-nortime','-turbo','-windowed','-run',str(out/'probe.xex')]
env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NS65_OUTPUT=str(out),NS65_CAPTURE='100,113,114,140',NS65_LIMIT='145',NSQ_PIN_SCHEDULE=str(out/'pins.csv'),UX1_REGISTER_LOG=str(out/'register-writes.csv'))
with (out/'emulator.log').open('w') as f:subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
samples=[]
for frame in [100,113,114,140]:
 ram=(out/f'frame-{frame:04}.ram').read_bytes();samples.append(dict(frame=frame,startup_marker=ram[0x3002],reset_marker=ram[0x3003],TRIG0=ram[0x3001]))
assert samples[1]['reset_marker']==0xa6 and samples[1]['TRIG0']==1 and all(q['TRIG0']==0 for q in samples[2:]),samples
js(out/'result.json',dict(status='PASS reset/repress retention',samples=samples,external_events=pins,target_sha256=sha(out/'probe.xex')))
gractl=rows(out/'control-writes.csv');edge=gractl[-1]['clock'];boundary=[]
for side in [-1,1]:
 pulse=edge+side-1;ss,where=micro(f'latch-reset-release-boundary-{side:+d}',code,[(4000200,15,0,7),(4000400,15,1,7),(pulse,15,0,7),(pulse+1,15,1,7)])
 expected=1 if side==-1 else 0;assert ss[-1]['TRIG0']==expected,(side,ss)
 boundary.append(dict(release_side=side,reenable_write_clock=edge,expected_after_release=expected,samples=ss))
held,_=micro('latch-held-low-across-enable',code,[(4000200,15,0,7),(4000400,15,1,7),(edge-1,15,0,7),(edge+1,15,1,7)])
assert held[-1]['TRIG0']==0
js(D/'latch-model-correction.json',dict(scope='Host model only, not a runtime fix or hardware qualification. Retention, reset/repress, pulse with no intervening evaluation, release at GRACTL-write boundary±1 and held-low-across-enable qualified; not arbitrary chip propagation/OS/hardware proof. Existing128/748 GRACTL0 traces not rebound.',corrected_source_sha256=sha(p),GTIA_source_sha256=sha(gtia),corrected_binary_sha256=sha(O/'src/atari800'),retention=ret,no_intervening_evaluation=dict(samples=short,pin_evaluations=events),reset_repress=samples,reset_boundaries=boundary,held_low_across_enable=held,original_defect='Reviewer micro-XEX observed seven low reads but no retained low after release.'))
print('PASS host latch retention/reset/repress; final runtime unchanged')
