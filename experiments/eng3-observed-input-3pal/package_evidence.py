"""Deliver final ATRs and lossless native PAL contact sheets with lineage."""
import json,hashlib,shutil,sys
from pathlib import Path
from native_image import Image,ImageDraw
B=Path('build/eng3-observed-input-3pal');D=Path('docs/checkpoints/art3-contextual-decoration');D.mkdir(exist_ok=True)
areas=json.loads((Path(__file__).parent/'areas.json').read_text())['areas'];records=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(dst,src,**kw):records.append(dict(file=str(dst),sha256=sha(dst),source=str(src),source_sha256=sha(src),**kw))
def crop(src,dst,**kw):Image.open(src).crop((8,24,328,216)).save(dst);record(dst,src,transform='native320x192 crop x8/y24, no resampling',**kw)
for spec in areas:
 a=spec['id'];root=B/f'area-{a}';out=D/f'area-{a}';media=out/'media';media.mkdir(parents=True,exist_ok=True)
 for name in ['candidate.atr','candidate.xex','candidate.lbl','candidate.map','carry.atr','scene-0.nrq','scene-1.nrq','scene-2.nrq','scene-0-banks.json','scene-1-banks.json','scene-2-banks.json','levels.json','solutions.json','packages.json','loading-art.json']:
  shutil.copy2(root/name,out/name)
 (out/'open').mkdir(exist_ok=True)
 for name in ['candidate.atr','candidate.lbl','candidate.xex','levels.json','solutions.json']:shutil.copy2(root/'open'/name,out/'open'/name)
 shutil.copytree(root/'reusable',out/'reusable',dirs_exist_ok=True)
 for name,sub in [('board.png','game-accepted-replay/native-0950.png'),('open.png','open/game-accepted-replay/native-0950.png'),('maximum-20x10.png','game-accepted-hud/native-0950.png'),('loading.png','loader-fast/native-0400.png')]:
  atr=root/('open/candidate.atr' if name=='open.png' else 'carry.atr' if name=='maximum-20x10.png' else 'candidate.atr')
  crop(root/sub,media/name,area=a,ATR=sha(atr))
 for kind in ['static','inverse','states','connections']:
  p=root/('atlas-'+kind);src=p/'capture/native-0950.png';meta=json.loads((p/'mutation.json').read_text())
  crop(src,media/f'atlas-{kind}.png',area=a,diagnostic_ATR=sha(p/'candidate.atr'),parent_ATR=sha(root/'candidate.atr'))
  shutil.copy2(p/'mutation.json',out/f'atlas-{kind}-mutation.json');shutil.copy2(p/'candidate.atr',out/f'atlas-{kind}.atr')
  if kind not in ['states','connections']:continue
  raw=Image.open(src)
  if kind=='states':entries=[v for vs in meta['bank_positions'].values() for v in vs];count=40;name='robot-40-native.png';w,h=320,96;cols=10
  else:entries=meta['bank_positions']['2'][12*4:];count=6;name='containers-docks-native.png';w,h=320,52;cols=6
  assert len(entries)==count*4
  sheet=Image.new('RGB',(w,h));draw=ImageDraw.Draw(sheet);draw.text((0,0),f'AREA {a} '+('ROBOT 0..39' if kind=='states' else 'BOX FULL EMPTY DOCK PHASE0..2'))
  for n in range(count):
   pos=entries[n*4]['position'];r,c=divmod(pos,40);im=raw.crop((8+c*8,24+r*8,24+c*8,40+r*8));x=n%cols*(32 if kind=='states' else 48);y=12+n//cols*20;sheet.paste(im,(x,y))
  sheet.save(media/name);record(media/name,src,area=a,diagnostic_ATR=sha(p/'candidate.atr'),transform='native16x16 displayed quads contact sheet; no reconstructed pixels',positions=entries)
 # Twelve consecutive frames show unchanged actual dock/robot/device animation.
 p=root/'game-accepted-dock';probe=json.loads((p/'dock-probe.json').read_text());start=probe['first_dock_action']['frame'];fs=list(range(start-1,start+11))
 sheet=Image.new('RGB',(1280,612));draw=ImageDraw.Draw(sheet);source=[]
 for n,f in enumerate(fs):
  src=p/f'native-{f:04}.png';x=n%4*320;y=n//4*204;draw.text((x,y),f'AREA {a} PAL FRAME {f}');sheet.paste(Image.open(src).crop((8,24,328,216)),(x,y+12));source.append(dict(path=str(src),sha256=sha(src)))
 dst=media/'animation-native.png';sheet.save(dst);record(dst,p/'artifact.json',area=a,ATR=sha(root/'candidate.atr'),transform='12 consecutive real PAL images; lossless crop/contact sheet',frames=source)
for name,file in [('four-areas-same-board','board.png'),('four-areas-open','open.png'),('four-areas-20x10','maximum-20x10.png'),('four-areas-loading','loading.png')]:
 for gray in [False,True]:
  sheet=Image.new('RGB',(640,408));draw=ImageDraw.Draw(sheet)
  for n,spec in enumerate(areas):
   src=D/f'area-{n+1}/media'/file;im=Image.open(src)
   if gray:im=im.convert('L').point(lambda v:min(255,85*round(v/85))).convert('RGB')
   x=n%2*320;y=n//2*204;draw.text((x,y),spec['name']);sheet.paste(im,(x,y+12))
  dst=D/(name+('-4-gray' if gray else '')+'.png');sheet.save(dst)
  records.append(dict(file=str(dst),sha256=sha(dst),sources=[str(D/f'area-{a}/media'/file) for a in range(1,5)],transform='lossless contact sheet'+('; Y=.299R+.587G+.114B rounded to 0/85/170/255' if gray else '')))
for file in ['robot-40-native.png','containers-docks-native.png']:
 height=96 if file.startswith('robot') else 52;sheet=Image.new('RGB',(640,height*2))
 for n in range(4):sheet.paste(Image.open(D/f'area-{n+1}/media'/file),(n%2*320,n//2*height))
 dst=D/file;sheet.save(dst);records.append(dict(file=str(dst),sha256=sha(dst),sources=[str(D/f'area-{a}/media'/file) for a in range(1,5)],transform='lossless contact sheet of native diagnostic quads'))
(D/'media-manifest.json').write_text(json.dumps(dict(classification='All gameplay/loader pixels are actual Atari800 PAL captures. Diagnostic atlases identified separately, original executable unchanged. Only crops, placement and declared four-gray conversion.',records=records),indent=2)+'\n')
for name in ['preflight.json','candidate-binding.json','byte-audit.json','resource-measurements.json','native-palette-audit.json','rebuild.json','proposal-measurements.json','art3-game-matrix.json','art3-media-matrix.json','art3-dock-matrix.json']:
 shutil.copy2(B/name,D/'evidence'/name)
shutil.copy2(Path(__file__).parent/'palette-oracle.json',D/'evidence/palette-oracle.json')
print('PASS delivered',len(records),'native image lineage records')
