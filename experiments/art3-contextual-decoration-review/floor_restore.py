"""Independent logical state and immutable package floor-restoration oracle."""
import argparse, hashlib, json, struct, re
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def crc(data):
 c=65535
 for byte in data:
  c^=byte<<8
  for _ in range(8):c=((c<<1)^0x1021 if c&32768 else c<<1)&65535
 return c
def packages(atr):
 cat=atr[400:528];assert cat[:6]==b'NSRD\x02\x05' and crc(cat[:126])==int.from_bytes(cat[126:],'little');out=[]
 for i in range(5):
  kind,flags,start,count,total,whole,zero,z=struct.unpack_from('<BB6H',cat,16+i*16);p=atr[16+(start-1)*128:16+(start-1)*128+total]
  assert crc(p)==whole and p[:6]==b'NSRQ\x02'+bytes([kind]);assert crc(p[:14])==int.from_bytes(p[14:16],'little');assert crc(p[16:144])==int.from_bytes(p[12:14],'little');assert crc(p[144:])==int.from_bytes(p[10:12],'little');sections={}
  for j in range(p[6]):
   address,n,off,c=struct.unpack_from('<4H',p,16+j*8);v=p[144+off:144+off+n];assert len(v)==n and crc(v)==c;sections[address]=v
  out.append(sections)
 return out
class Model:
 def __init__(self,rows):
  self.rows=rows;self.walls={(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c=='#'};self.goals={(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '.*+'};self.boxes={(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '$*'};self.player=next((x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '@+');self.history=[]
 def occupied(self):return self.boxes|{self.player}
 def action(self,key):
  before=self.occupied()
  if key=='Z':
   if self.history:self.player,self.boxes=self.history.pop()
  else:
   dx,dy={'U':(0,-1),'D':(0,1),'L':(-1,0),'R':(1,0)}[key];p=(self.player[0]+dx,self.player[1]+dy);q=(p[0]+dx,p[1]+dy)
   if p not in self.walls and not(p in self.boxes and(q in self.walls or q in self.boxes)):
    self.history.append((self.player,set(self.boxes)))
    if p in self.boxes:self.boxes.remove(p);self.boxes.add(q)
    self.player=p
  return before-self.occupied()
def one(root,area,fixture,source):
 p=root/f'area-{area}-{fixture}';atr=(p/'snapshot.atr').read_bytes();s=packages(atr)[1 if fixture=='maximum' else 0];desc=s[0x9de0];w,h,bx,by=desc[:4];rows=(source/({'obstacles':'energy-service-bay-obstacles-v1.xsb','open':'energy-service-bay-open-regression.xsb','maximum':'maximum-20x10-regression.xsb'}[fixture])).read_text().splitlines();assert (w,h)==(len(rows[0]),len(rows));m=Model(rows)
 if (p/'floor-walk.json').exists():actions=[(v['capture'],v['action']) for v in json.loads((p/'floor-walk.json').read_text())['actions']]
 elif fixture=='obstacles':
  path=(source/'energy-service-bay-obstacles-v1.solution').read_text().strip();actions=[(1108+i*12,k) for i,k in enumerate(path)]+[(2008+i*12,'Z') for i in range(len(path))]
 else:actions=[(1110+i*20,k) for i,k in enumerate('URRDL' if fixture=='maximum' else 'URRDLUD')]
 labels={n:int(v,16) for v,n in re.findall(r'^al (\w+) \.(\w+)',(p/'candidate.lbl').read_text(),re.M)}
 counts={'floor_quarters':0,'vacated_floor_cells':0,'vacated_patterned_cells':0,'vacated_crossbank_cells':0,'vacated_patterned_crossbank_cells':0};cross=set();vacated=[]
 for frame,key in [(1000,None)]+actions:
  freed=m.action(key) if key else set();state=(p/f'frame-{frame:04}.ram').read_bytes();g=labels['_gs'];assert tuple(state[g+762:g+764])==m.player and {tuple(state[g+764+i*2:g+766+i*2]) for i in range(state[g+784])}==m.boxes,(area,fixture,frame,'independent state mismatch');assert int.from_bytes(state[labels['_count']:labels['_count']+2],'little')==len(m.history)
  ram=(p/f'raster-{frame:04}.ram').read_bytes()
  assert ram[0x1400:0x1720]==s[0x1400],(area,fixture,frame,'composition modified at runtime')
  for y in range(h):
   for x in range(w):
    if (x,y) in m.walls|m.goals|m.occupied():continue
    codes=s[0x1400][(y*20+x)*4:(y*20+x)*4+4];banks=[];pattern=False
    for q,code in enumerate(codes):
     row=by+y*2+q//2;bank=min((row-2)//4,4);addr=[0x8c00,0xa000,0xa400,0xa800,0xac00][bank];pos=0x8800+row*40+bx+x*2+q%2;banks.append(bank)
     assert ram[pos]==code,(area,fixture,frame,x,y,q,'floor code',ram[pos],code)
     glyph=s[addr][(code&127)*8:(code&127)*8+8];assert ram[addr+(code&127)*8:addr+(code&127)*8+8]==glyph,(area,fixture,frame,x,y,q,'floor glyph');pattern|=any(glyph);counts['floor_quarters']+=1
    if (x,y) in freed:
     counts['vacated_floor_cells']+=1;counts['vacated_patterned_cells']+=int(pattern)
     if len(set(banks))>1:counts['vacated_crossbank_cells']+=1;counts['vacated_patterned_crossbank_cells']+=int(pattern);cross.add(tuple(sorted(set(banks))))
     vacated.append({'frame':frame,'action':key,'cell':[x,y],'codes':list(codes),'banks':banks,'patterned':bool(pattern)})
 assert counts['vacated_floor_cells']>0,(area,fixture,counts)
 return {'area':area,'fixture':fixture,'ATR':hashlib.sha256(atr).hexdigest(),'status':'PASS','patterned_restoration_covered':counts['vacated_patterned_cells']>0,'counts':counts,'crossbank_pairs':sorted(cross),'vacated':vacated,'oracle':'Independent XSB state+immutable package COMPOSITION, compared to actual raster RAM screen and bank glyphs; no candidate renderer import.'}
def main():
 a=argparse.ArgumentParser();a.add_argument('--captures',default='build/art2-neon-palettes-review/candidate-v2');a.add_argument('--source',default='experiments/art2-neon-palettes');a.add_argument('--output',default='build/art3-contextual-decoration-review/base-floor-restoration.json');args=a.parse_args();r=[one(R/args.captures,n,f,R/args.source) for n in range(1,5) for f in ['obstacles','open','maximum']];out=R/args.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'status':'PASS','cases':r},indent=2)+'\n');print(json.dumps([{'area':x['area'],'fixture':x['fixture'],**x['counts'],'crossbank':x['crossbank_pairs']} for x in r],indent=2))
if __name__=='__main__':main()
