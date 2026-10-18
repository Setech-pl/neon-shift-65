"""Exhaustive ART3 byte delta; allocation and scope verified against ART2.1."""
import hashlib,json,re,struct,sys
from pathlib import Path
sys.path.insert(0,'experiments/eng3-observed-input-3pal-review')
from floor_restore import packages
S=Path(__file__).parent;B=Path('build/eng3-observed-input-3pal');OLD=Path('build/art2-neon-palettes')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def labels(p):return {n:int(h,16) for h,n in re.findall(r'^al (\w+) \.(\w+)',p.read_text(),re.M)}
results=[];resources=[]
for area in range(1,5):
 rv=[]
 for fixture in ['', 'open']:
  old=OLD/f'area-{area}'/fixture;new=B/f'area-{area}'/fixture
  for name in ['menu.nrq','music.nrq','splash.nrq','loading-art.bin','splash-bitmap.bin','early-packed.bin']:
   if (old/name).exists():assert (old/name).read_bytes()==(new/name).read_bytes(),name
  for variant in ['candidate','dim','stress','carry','wrap','counter9','counter99','counter999']:
   ap=old/(variant+'.atr');bp=new/(variant+'.atr');a=ap.read_bytes();b=bp.read_bytes();assert len(a)==len(b)==1048592
   assert (old/(variant+'.xex')).read_bytes()==(new/(variant+'.xex')).read_bytes()
   assert labels(old/(variant+'.lbl'))==labels(new/(variant+'.lbl'))
   allowed={};changes=[]
   for i in [424,425,440,441,456,457,526,527]:allowed[i]=('checksum','catalog package/directory CRC16')
   for j in range(3):
    ka,fa,sa,ca,na,*_=struct.unpack_from('<BB6H',a,416+j*16);kb,fb,sb,cb,nb,*_=struct.unpack_from('<BB6H',b,416+j*16)
    assert (ka,fa,sa,ca,na)==(kb,fb,sb,cb,nb);start=16+(sa-1)*128;pa=a[start:start+na];pb=b[start:start+nb];assert na==8768
    for i in range(10,16):allowed[start+i]=('checksum','NRQ payload/table/header CRC16')
    for k in range(pa[6]):
     addr,n,off,crc=struct.unpack_from('<4H',pa,16+k*8);addr2,n2,off2,crc2=struct.unpack_from('<4H',pb,16+k*8);assert (addr,n,off)==(addr2,n2,off2)
     for i in range(6,8):allowed[start+16+k*8+i]=('checksum','section CRC16')
     if addr in [0x8c00,0xa000,0xa400,0xa800,0xac00]:kind='bank';detail='static patterns/reallocation; actor and animation patterns separately decoded and checked'
     elif addr==0x1400:kind='composition';detail='board quarter codes selected offline'
     elif addr==0x9800:kind='background';detail='background screen quarter codes'
     elif addr==0x9de0:kind='descriptor';detail='remapped actor codes and relocated animation address/codes, fixed sequence/period/phase'
     else:
      assert pa[144+off:144+off+n]==pb[144+off:144+off+n],(area,fixture,variant,addr);continue
     for i in range(n):
      if kind=='descriptor' and not 8<=i<536:continue
      allowed[start+144+off+i]=(kind,detail)
   for i,(v,w) in enumerate(zip(a,b)):
    if v!=w:
     assert i in allowed,(area,fixture,variant,i,v,w);kind,detail=allowed[i];changes.append(dict(offset=i,old=v,new=w,kind=kind))
   nl=labels(new/(variant+'.lbl'));rv.append(dict(fixture=fixture or 'obstacles',variant=variant,MAIN_free=32768-nl['__BSS_RUN__']-nl['__BSS_SIZE__'],LOW_free=5120-nl['__LOADBSS_RUN__']-nl['__LOADBSS_SIZE__'],ZP_free=256-nl['__ZP_LAST__']))
   results.append(dict(area=area,fixture=fixture or 'obstacles',variant=variant,old=sha(ap),candidate=sha(bp),bytes=len(b),counts={k:sum(c['kind']==k for c in changes) for k in ['bank','composition','background','descriptor','checksum']},palette_bytes=0,resident_bytes=0,unclassified_bytes=0,changes=changes))
 oldres=json.loads((OLD/'resource-measurements.json').read_text())[area-1];banks={}
 for f in ['', 'open']:
  for scene in range(3):banks[f'{f or "obstacles"}-scene-{scene}']=json.loads((B/f'area-{area}'/f/f'scene-{scene}-banks.json').read_text())
 resources.append(dict(area=area,variants=rv,banks=banks,active_pack=oldres['active_pack'],RAM=oldres['RAM'],disk_bytes=1048592,allocated_sectors=507,min_free_glyphs=min(b['free'] for sc in banks.values() for b in sc['banks']),method='Fresh exact resident XEX and identical labels/reservations; fixed NRQ section extents. Historical lifetime union remains valid, without claiming old CPU timings as new measurements.'))
(B/'byte-audit.json').write_text(json.dumps(dict(status='PASS',ATR_comparisons=64,unclassified_bytes=0,results=results),indent=2)+'\n')
(B/'resource-measurements.json').write_text(json.dumps(resources,indent=2)+'\n')
print('PASS64 ATR: scene data + CRC only;0 palette/resident bytes; identical reservations')
