"""Lossless native RGB crops/contact sheets using local PNG reader + NumPy.

No generative/resampling renderer is involved. Text labels live outside crops.
"""
import json,struct,zlib,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'tools')
from m1_check import png
class Image:
 def __init__(self,pixels):self.pixels=np.array(pixels,dtype=np.uint8)
 @classmethod
 def open(cls,path):
  path=Path(path);raw=path.read_bytes();w,h,depth,kind,_,_,_=struct.unpack('>IIBBBBB',raw[16:29])
  if kind==3:
   pixels,palette=png(path);return cls(np.array(palette,dtype=np.uint8)[np.array(pixels,dtype=np.uint8)])
  assert depth==8 and kind==2
  pos=8;data=b''
  while pos<len(raw):
   n=int.from_bytes(raw[pos:pos+4],'big');tag=raw[pos+4:pos+8]
   if tag==b'IDAT':data+=raw[pos+8:pos+8+n]
   pos+=n+12
  scan=np.frombuffer(zlib.decompress(data),dtype=np.uint8).reshape(h,1+w*3);assert not np.any(scan[:,0])
  return cls(scan[:,1:].reshape(h,w,3))
 @classmethod
 def new(cls,mode,size):return cls(np.zeros((size[1],size[0],3),dtype=np.uint8))
 def convert(self,mode):
  if mode=='L':return Image(np.rint(self.pixels.astype(float)@np.array([.299,.587,.114])).astype(np.uint8))
  if self.pixels.ndim==2:return Image(np.repeat(self.pixels[:,:,None],3,axis=2))
  return Image(self.pixels)
 def point(self,f):return Image(np.array([f(i) for i in range(256)],dtype=np.uint8)[self.pixels])
 def crop(self,box):x,y,z,w=box;return Image(self.pixels[y:w,x:z])
 def paste(self,other,xy):x,y=xy;h,w=other.pixels.shape[:2];self.pixels[y:y+h,x:x+w]=other.pixels
 def save(self,path):
  h,w=self.pixels.shape[:2];assert self.pixels.ndim==3
  def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
  scan=b''.join(b'\0'+row.tobytes() for row in self.pixels)
  Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b''))
class Draw:
 def __init__(self,im):self.im=im
 def text(self,xy,text,fill='white'):
  x,y=xy;font=json.loads(Path('assets/graphics/mono-font.json').read_text())['menu_rows_hex']
  for c in text.upper():
   data=bytes.fromhex(font.get(c,'00000000000000'))
   for yy,v in enumerate(data):
    for xx in range(8):
     if v&(128>>xx) and y+yy<self.im.pixels.shape[0] and x+xx<self.im.pixels.shape[1]:self.im.pixels[y+yy,x+xx]=(255,255,255)
   x+=8
class ImageDraw:Draw=Draw
