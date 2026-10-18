"""Vectorized equivalent of the native ANTIC oracle, same PNG palette."""
import numpy as np
from pathlib import Path
from verify import png
def pixel(out,frame,l):
    out=Path(out);raw=(out/f'raster-{frame:04}.ram').read_bytes();r=np.frombuffer(raw,dtype=np.uint8)
    im,pal=png(out/f'native-{frame:04}.png');im=np.array(im,dtype=np.uint8);pal=np.array(pal)
    blank=bool(np.all(pal[im[24:216,8:328]]==pal[r[0x2c8]]))
    previous=out/f'raster-{frame-1:04}.ram'
    reactivating=bool(previous.exists() and not previous.read_bytes()[l['_display_active']] and r[l['_display_active']])
    if not r[l['_display_active']] and not r[0x22f]:
        assert blank
        return dict(frame=frame,pixels=320*192,status='PASS',mode='complete DMA-off')
    if reactivating and blank:return dict(frame=frame,pixels=320*192,status='PASS',mode='reactivation blank')
    colors=[int(r[0x2c8])]+list(map(int,r[0x2c4:0x2c8]));colors[2]=int(r[l['_display_pf1']]);colors[3]=int(r[l['_display_pf2']])
    bank=int(r[l['_display_font']])*256;dl=0x9f60;y=0;address=0;dli=0;points=0
    while True:
        op=int(r[dl]);dl+=1;mode=op&15
        if mode==1:break
        if mode==0:
            h=((op>>4)&7)+1
            if y>=24:assert np.all(pal[im[y:y+h,8:328]]==pal[colors[0]])
            y+=h;continue
        assert mode in (2,4,14,15)
        if op&64:address=int(r[dl])|(int(r[dl+1])<<8);dl+=2
        h=1 if mode in (14,15) else 8
        if mode==14:
            pp=(r[address:address+40,None]>>np.array([6,4,2,0]))&3
            want=np.repeat(np.array(colors)[pp.reshape(1,160)],2,axis=1)
        elif mode==15:
            bits=np.unpackbits(r[address:address+40]).reshape(1,320)
            want=np.where(bits,(colors[3]&240)|(colors[2]&15),colors[3])
        else:
            codes=r[address:address+40];v=r[bank+(codes.astype(np.uint16)&127)[:,None]*8+np.arange(8)].T
            if mode==2:
                bits=((v[:,:,None]>>np.arange(7,-1,-1))&1)^((codes[None,:,None]&128)!=0)
                want=np.where(bits,(colors[3]&240)|(colors[2]&15),colors[3]).reshape(8,320)
            else:
                pp=(v[:,:,None]>>np.array([6,4,2,0]))&3
                ci=np.where((pp==3)&((codes[None,:,None]&128)!=0),4,pp)
                want=np.repeat(np.array(colors)[ci].reshape(8,160),2,axis=1)
        assert np.all(pal[im[y:y+h,8:328]]==pal[want]),(frame,y,mode,'native pixel mismatch')
        points+=320*h;address+=40;y+=h
        if op&128:
            bank=int(r[l['_dli_font']+dli])*256;colors[2]=int(r[l['_dli_pf1']+dli]);colors[3]=int(r[l['_dli_pf2']+dli]);dli+=1
    assert y==216
    return dict(frame=frame,pixels=points,dlis=dli,status='PASS')
