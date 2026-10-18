"""Independent declared Atari colors plus real native PAL rasters/attributes."""
import json,re,sys,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,'tools');from m1_check import png
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal');O=Path('build/art2-neon-palettes');spec=json.loads((S/'palette-oracle.json').read_text())['areas']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def labels(p):return {n:int(h,16) for h,n in re.findall(r'^al (\w+) \.(\w+)',p.read_text(),re.M)}
report=[]
for a in range(1,5):
 root=B/f'area-{a}';e=spec[str(a)];palette=e['palette'];cases=[]
 for case in ['game-accepted-replay','game-accepted-hud','open/game-accepted-replay','game-accepted-dock']:
  d=root/case;l=labels(d/'candidate.lbl');checked=0;pixels=0;counts={};unchanged=0;different=0
  for p in sorted(d.glob('native-*.png')):
   f=p.stem.split('-')[-1];ram=(d/f'raster-{f}.ram').read_bytes()
   if ram[l['_phase']] not in [1,2] or ram[l['_asset_loading']] or not ram[l['_display_active']]:continue
   assert list(ram[0x2c4:0x2c9])==palette,(a,case,f,'OS palette')
   assert ram[l['_display_pf1']]==14 and ram[l['_display_pf2']]==e['hud_pf2']
   assert list(ram[l['_dli_pf1']:l['_dli_pf1']+6])==[14]+[palette[1]]*5
   assert list(ram[l['_dli_pf2']:l['_dli_pf2']+6])==[0]+[palette[2]]*5
   im,pal=png(p);im=np.array(im);pal=np.array(pal);game=im[40:216,8:328]
   colors=np.unique(game);allowed={tuple(pal[c]) for c in palette}
   assert all(tuple(pal[c]) in allowed for c in colors),(a,case,f,colors)
   for c in colors:counts[str(int(c))]=counts.get(str(int(c)),0)+int(np.count_nonzero(game==c))
   if a!=1:
    # Native pixels must use the declared single hue or black, in every strip.
    assert all(c==0 or c>>4==palette[0]>>4 for c in colors),(a,case,f,colors)
   ref=O/f'area-{a}'/case/p.name
   if ref.exists():
    old,oldpal=png(ref);old=np.array(old);oldpal=np.array(oldpal)
    diff=int(np.count_nonzero(np.any(oldpal[old[24:216,8:328]]!=pal[im[24:216,8:328]],axis=2)))
    if diff:different+=1
    else:unchanged+=1
   checked+=1;pixels+=game.size
  assert checked>0
  cases.append(dict(case=case,frames=checked,pixels=pixels,Atari_palette_usage=counts,before_identical_images=unchanged,before_different_images=different))
 report.append(dict(area=a,ATR=sha(root/'candidate.atr'),palette=palette,cases=cases,unapproved_colors=0,fixture_status='PASS'))
result=dict(status='PASS',oracle=sha(S/'palette-oracle.json'),method='Assert shadow + initial/DLI color arrays against independently declared palette. Check all actual PAL native gameplay pixels in every band; no RGB oracle taken from candidate screen. Palette from frozen independent ART2.1 specification; ART3 intentionally changes composition.',areas=report)
(B/'native-palette-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS native palette',sum(c['frames'] for a in report for c in a['cases']),'frames; area1 different',sum(c['before_different_images'] for c in report[0]['cases']))
