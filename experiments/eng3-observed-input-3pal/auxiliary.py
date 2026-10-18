"""Final-ATR loaders, glyph atlas derivatives, and active metadata provenance."""
import json,os,sys,struct,hashlib,shutil,csv
from pathlib import Path
area=int(sys.argv[1]);mode=sys.argv[2];B=Path(f'build/eng3-observed-input-3pal/area-{area}')
os.environ['NEON_A5C_BUILD']=str(B)
sys.path.insert(0,str(Path('experiments/renderer-a5c').resolve()))
import gauntlet,verify,fetch_oracle,pixel_fast,turbo_run
from emulator_smoke import run as native
from m1_check import png
from warehouses import crc16
from atr import offset
os.environ['NEON_A5B_OBSERVER']=str(Path('build/ux1-menu-splash-loader-crates-review/observer-v2/src/atari800').resolve())
verify.pixel_reference=pixel_fast.pixel
def probe(name,events,caps,total,root=B,variant='candidate',patch=True):
 gauntlet.ROOT=root
 dest=root/name
 def run(n,*args,**kw):kw['boot']=True;return native(str(dest.relative_to('build')),*args,**kw)
 gauntlet.run=run
 os.environ['NSQ_FETCH_RANGE']=f'{min(caps)},{max(caps)}'
 os.environ['UX1_REGISTER_LOG']=str((dest/'register-writes.csv').resolve())
 os.environ['UX1_REGISTER_RANGE']='1,2500'
 return gauntlet.probe(name,events,caps,total,boot=True,variant=variant,patch=patch)
def section(b):return {a:b[144+o:144+o+n] for a,n,o,c in [struct.unpack_from('<4H',b,16+i*8) for i in range(b[6])]}
def atlas(inverse=False,states=False,canonical=False):
 root=B/('atlas-connections' if canonical else 'atlas-states' if states else 'atlas-inverse' if inverse else 'atlas-static');root.mkdir(exist_ok=True)
 data=(B/'scene-0.nrq').read_bytes();sections=section(data);desc=bytearray(sections[0x9de0]);desc[4]=0;desc[128:536]=bytes(408)
 rows=json.loads((B/'levels.json').read_text())['levels'][0]['rows'];w,h,bx,by=desc[:4]
 screen=bytearray(sections[0x9800]);composition=bytearray(sections[0x1400]);positions={};excluded=set()
 for y,row in enumerate(rows):
  for x,v in enumerate(row):
   if v in '@$.*+':excluded.update((by+y*2+q//2)*40+bx+x*2+q%2 for q in range(4))
 banks=[0x8c00,0xa000,0xa400,0xa800,0xac00]
 for i,addr in enumerate(banks):
  positions[i]=[pos for pos in range((2+4*i)*40,min((6+4*i)*40,960)) if pos not in excluded]
  if canonical and i<3:
   readtiles=lambda name:[t for t in [(B/'reusable'/name).read_bytes()[n:n+32] for n in range(0,(B/'reusable'/name).stat().st_size,32)]]
   tiles=readtiles('walls.bin')[i*16:(i+1)*16] if i<2 else readtiles('floors.bin')+readtiles('objects.bin')
   objects=readtiles('objects.bin');glyphs=[bytes(8)];indices={bytes(8):0}
   def intern(v):
    if v not in indices:indices[v]=len(glyphs);glyphs.append(v)
    assert len(glyphs)<=124
    return indices[v]
   for n,t in enumerate(objects):
    for q in range(4):desc[8+i*24+n*4+q]=intern(t[q*8:q*8+8])|(0 if n==2 else 128)
   codes=[intern(t[q*8:q*8+8])|(128 if i==2 and n>=12 and n!=14 else 0) for n,t in enumerate(tiles) for q in range(4)]
   sections[addr]=b''.join(glyphs)+bytes(1024-len(glyphs)*8)
   anchors=[r*40+col for r in (2+4*i,4+4*i) for col in range(0,40,2) if all(r*40+col+q%2+(q//2)*40 not in excluded for q in range(4))][:len(tiles)]
   assert len(anchors)==len(tiles)
   positions[i]=[p+q%2+(q//2)*40 for p in anchors for q in range(4)]
  elif states:
   # Copy frozen source quarters into normal slots, preserving all object
   # quarter codes used at initial box/dock locations in this strip.
   bank=bytearray(sections[addr]);reserved={v&127 for v in desc[8+i*24:8+(i+1)*24]}
   codes=[v for v in range(1,124) if v not in reserved][:32]
   assert len(codes)==32
   for n,code in enumerate(codes):bank[code*8:(code+1)*8]=sections[0xb160][i*256+n*8:i*256+(n+1)*8]
   sections[addr]=bytes(bank)
   anchors=[r*40+col for r in (2+4*i,4+4*i) for col in range(0,40,2) if all(r*40+col+q%2+(q//2)*40 not in excluded for q in range(4))][:8]
   assert len(anchors)==8
   positions[i]=[p+q%2+(q//2)*40 for p in anchors for q in range(4)]
  else:codes=list(range(124))
  assert len(positions[i])>=len(codes)
  for pos in range((2+4*i)*40,min((6+4*i)*40,960)):
   if pos not in excluded:screen[pos-80]=0
  for pos,code in zip(positions[i],codes):screen[pos-80]=code|(128 if inverse else 0)
  positions[i]=[dict(position=p,code=c|(128 if inverse else 0),source_frame=i*8+n//4 if states else None,quarter=n%4 if states else None) for n,(p,c) in enumerate(zip(positions[i],codes))]
 for y in range(h):
  for x in range(w):
   for q in range(4):composition[(y*20+x)*4+q]=screen[(by+y*2+q//2)*40+bx+x*2+q%2-80]
 sections[0x9de0]=bytes(desc);sections[0x9800]=bytes(screen);sections[0x1400]=bytes(composition)
 rebuilt=bytearray(data[:144]);body=b''.join(sections.values());off=0
 for i,(addr,payload) in enumerate(sections.items()):struct.pack_into('<4H',rebuilt,16+i*8,addr,len(payload),off,crc16(payload));off+=len(payload)
 struct.pack_into('<H',rebuilt,10,crc16(body));struct.pack_into('<H',rebuilt,12,crc16(rebuilt[16:]));struct.pack_into('<H',rebuilt,14,crc16(rebuilt[:14]));rebuilt+=body
 image=bytearray((B/'candidate.atr').read_bytes());image[offset(512,128):offset(512,128)+len(rebuilt)]=rebuilt
 directory=bytearray(image[offset(4,128):offset(4,128)+128]);struct.pack_into('<H',directory,24,crc16(rebuilt));struct.pack_into('<H',directory,126,crc16(directory[:126]));image[offset(4,128):offset(4,128)+128]=directory
 (root/'candidate.atr').write_bytes(image)
 for suffix in ['.lbl','.xex']:shutil.copyfile(B/('candidate'+suffix),root/('candidate'+suffix))
 (root/'mutation.json').write_text(json.dumps(dict(classification='Diagnostic ATR derivative; compiled scene data only, physical input and unchanged final code',parent_SHA256=hashlib.sha256((B/'candidate.atr').read_bytes()).hexdigest(),SHA256=hashlib.sha256(image).hexdigest(),inverse=inverse,all_40_robot_states=states,canonical_connections_and_objects=canonical,bank_positions=positions,animations_disabled=True,actual_renderer='same ANTIC4 five strips, same logical fixture and show_play'),indent=2)+'\n')
 p=probe('capture',[(700,700,{'fire':0})],[950],1000,root)
 fetch_oracle.check(p,[950])
def loader(patch):
 name='loader-fast' if patch else 'loader-slow';start=700 if patch else 1900
 caps=sorted(set([400,500,680,800,950]+list(range(360,550,8)))) if patch else [500,800,1200,1700,1800,2000,2100,2400]
 p=probe(name,[(start,start,{'fire':0})],caps,1050 if patch else 2450,patch=patch)
 (p/'loader-result.json').write_text(json.dumps(dict(ATR=json.loads((p/'artifact.json').read_text())['ATR'],area=area,mode='ANTIC C 160x64, doubled horizontal native pixels',captures=caps,source='1280B stage2 at $ba00 in final cold ATR stream',status='CAPTURED'),indent=2)+'\n')
if mode=='loader':loader(True);loader(False)
elif mode=='atlas':atlas();atlas(True);atlas(states=True)
elif mode=='connections':atlas(canonical=True)
else:raise ValueError(mode)
