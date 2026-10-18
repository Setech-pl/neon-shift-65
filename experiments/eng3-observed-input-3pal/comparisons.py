"""Label real historical/final PAL images and build native headless replay films."""
import hashlib,json,subprocess
from pathlib import Path
from native_image import Image,ImageDraw
D=Path('docs/checkpoints/art3-contextual-decoration/evidence');B=Path('build/eng3-observed-input-3pal');D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
fixtures=[('16x8','game-accepted-replay','candidate'),('open','open/game-accepted-replay','open/candidate'),('20x10','game-accepted-hud','carry')]
for kind,roots in [('before-after',['art2-neon-palettes','art3-contextual-decoration']),('provenance-art2-art21',['art2-four-area-themes','art2-neon-palettes'])]:
 for fixture,case,variant in fixtures:
  for gray in ([False,True] if kind=='before-after' else [False]):
   sheet=Image.new('RGB',(640,960));draw=ImageDraw.Draw(sheet);sources=[]
   for area in range(1,5):
    for col,root in enumerate(roots):
     base=Path('build')/root/f'area-{area}';src=base/case/'native-0950.png';atr=base/(variant+'.atr');h=sha(atr)
     meta=json.loads((base/case/'artifact.json').read_text());assert meta['ATR']['sha256']==h
     im=Image.open(src).crop((8,24,328,216))
     if gray:im=im.convert('L').point(lambda v:85*round(v/85)).convert('RGB')
     x=col*320;y=(area-1)*240
     label=('ART2.1' if root=='art2-neon-palettes' else 'ART3' if root=='art3-contextual-decoration' else 'ART2')
     for line,text in enumerate([f'{label} AREA {area} {fixture} PAL950',h[:32],h[32:]]):draw.text((x,y+line*12),text)
     sheet.paste(im,(x,y+44));sources.append(dict(area=area,fixture=fixture,checkpoint=label,ATR=str(atr),ATR_SHA256=h,native=str(src),native_SHA256=sha(src),capture=950,artifact_SHA256=sha(base/case/'artifact.json')))
   out=D/(kind+'-'+fixture+('-4-gray' if gray else '')+'.png');sheet.save(out);records.append(dict(file=str(out),sha256=sha(out),sources=sources,transform='native x8/y24 320x192 crop, labels outside image; '+('Y=.299R+.587G+.114B -> nearest0/85/170/255' if gray else 'no resampling')))
for a in range(1,5):
 root=B/f'area-{a}/native-film';out=D/f'area-{a}-headless-replay.mp4'
 cmd=['ffmpeg','-y','-v','error','-framerate','1773447/35568','-start_number','950','-i',str(root/'native-%04d.png'),'-i',str(root/'native-audio.wav'),'-map','0:v','-an','-frames:v','351','-vf','crop=320:192:8:24','-c:v','libx264rgb','-crf','0','-preset','fast',str(out)]
 subprocess.run(cmd,check=True)
 records.append(dict(file=str(out),sha256=sha(out),ATR_SHA256=sha(B/f'area-{a}/candidate.atr'),frames=[950,1300],PAL_fps='1773447/35568',source_frames={p.name:sha(p) for f in range(950,1301) for p in [root/f'native-{f:04}.png']},audio='No audio track; PCM separately machine validated, listening NOT_RUN',transform='lossless RGB crop and lossless H264RGB; native PAL speed',command=cmd))
(D/'comparison-manifest.json').write_text(json.dumps(dict(status='PASS',screenshot_identity='Owner screenshot files not provided; verbal colors resemble ART2. No claim of exact identity.',records=records),indent=2)+'\n')
print('PASS',len(records),'labeled comparisons/films')
