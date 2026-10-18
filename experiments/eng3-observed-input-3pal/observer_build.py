"""Read-only device-query logging, in a separate Atari800 source tree."""
from pathlib import Path
import shutil,subprocess,json,hashlib
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent
B=R/'build/eng3-observed-input-3pal';O=B/'observer'
old=R/'build/ux1-menu-splash-loader-crates-review/observer-v2'
assert not O.exists()
shutil.copytree(old,O,ignore=shutil.ignore_patterns('*.o','.deps','atari800'))
for stem,func in [('pia','PIA'),('gtia','GTIA')]:
 p=O/'src'/f'{stem}.c';t=p.read_text();sig=f'UBYTE {func}_GetByte(UWORD addr, int no_side_effects)'
 assert t.count(sig)==1
 t=t.replace(sig,f'static UBYTE ENG2_{func}_GetByte(UWORD addr, int no_side_effects)')
 t+='\nextern void ENG2_Read(UWORD addr, UBYTE value, int peek);\n'+sig+'\n{\n UBYTE v=ENG2_'+func+'_GetByte(addr,no_side_effects);\n ENG2_Read(addr,v,no_side_effects);\n return v;\n}\n'
 p.write_text(t)
p=O/'src/neon_trace.h'
with p.open('a') as f:f.write(r'''
/* ENG2: actual device handler returns, excluding observer peeks. No target cycles. */
void ENG2_Read(UWORD addr, UBYTE value, int peek)
{
 static FILE *f;static int init;static unsigned lo,hi;
 unsigned frame=(unsigned)Atari800_nframes+1;
 if(!init){const char *v=getenv("ENG2_BUS_RANGE");init=1;if(v)sscanf(v,"%u,%u",&lo,&hi);}
 if(peek || !lo || frame<lo || frame>hi || !(addr==0xd300 || addr==0xd010 || addr==0xd01f))return;
 if(!f){char path[1024];snprintf(path,sizeof(path),"%s/device-reads.csv",ns65_dir);f=fopen(path,"w");
  if(f)fprintf(f,"frame,clock,ypos,xpos,address,value,pactl,ddra_mask,gractl,trigger_latch\n");}
 if(f)fprintf(f,"%u,%llu,%u,%d,%u,%u,%u,%u,%u,%u\n",frame,(unsigned long long)ANTIC_CPU_CLOCK,
  (unsigned)ANTIC_ypos,ANTIC_xpos,addr,value,PIA_PACTL,PIA_PORTA_mask,GTIA_GRACTL,GTIA_TRIG_latch[0]);
}
''')
# The preserved configured makefiles use relative sources; don't reconfigure.
with (B/'observer-build.log').open('w') as log:
 subprocess.run(['make','-C',str(O/'src'),'-j3'],stdout=log,stderr=subprocess.STDOUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={str(p.relative_to(O)):sha(p) for p in (O/'src').glob('*') if p.suffix in ('.c','.h')}
(B/'observer-manifest.json').write_text(json.dumps(dict(source=manifest,binary=sha(O/'src/atari800'),instrumentation='Host only: zero emulated CPU cycles. Device query clocks are Atari800 model times, not physical pin propagation proof. Existing side-effect-free audit peeks excluded; GRACTL unchanged.'),indent=2)+'\n')
print('ENG2 observer',O/'src/atari800')
