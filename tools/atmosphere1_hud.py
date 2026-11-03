import sys
sys.path.insert(0,'tools')
import atmosphere1_verify as t
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import numpy as np,json
F=json.loads((t.DOC/'fixtures.json').read_text())
def run(n):
 mode=f'{n:02}';ev=[(4650+i*10,4650+i*10,dict(stick=t.STICK[ch])) for i,ch in enumerate(F['openings'][str(n)])]
 old=(t.ROOT/'build/atmosphere1-baseline/candidate.atr').read_bytes()
 o,ss,l=t.probe('hud-baseline-'+mode,'normal',[(3200,3200,dict(fire=0))]+ev if n==1 else [(3200,3200,dict(stick=13)),(3250,3250,dict(fire=0))]+ev,[4500,4819],4830,baseline=True,image=None if n==1 else t.save_image(old,n))
 after=t.BASE/('runs/audio-real-'+mode)
 for f in (4500,4819):
  a=np.array(Image.open(o/f'native-{f:04}.png').convert('RGB'));b=np.array(Image.open(after/f'native-{f:04}.png').convert('RGB'))
  assert np.array_equal(a[24:40],b[24:40]),(n,f,'HUD differs')
 return dict(level=n,initial_and_after_movement_HUD_identical=True)
with ThreadPoolExecutor(max_workers=4) as pool:rs=list(pool.map(run,(1,16,31,46)))
t.dump(t.DOC/'hud.json',dict(status='PASS',records=rs))
