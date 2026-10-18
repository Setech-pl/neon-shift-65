"""Code-native NEON artwork and pinned declarative cassette compiler."""
import json,subprocess,struct
from pathlib import Path

def generate(c):
    out=c.OUT;ref=Path('experiments/startup-l0/reference/ef1924d')
    audio=Path(__file__).parent/'boot-splash.json'
    if not audio.exists():raise RuntimeError('Missing declarative audio')
    js='''import fs from 'node:fs';
import {packBroadsideLzss,unpackBroadsideLzss} from './experiments/eng3-observed-input-3pal/reference/broadside-lzss.mjs';
import {loadBootSplashDefinition,renderBootSplashCa65Include} from './experiments/eng3-observed-input-3pal/reference/boot-splash-assets.mjs';
const out=process.argv[1], audio=process.argv[2];
fs.writeFileSync(out+'/boot-splash.inc',renderBootSplashCa65Include(loadBootSplashDefinition(audio)));
const menu=fs.readFileSync(out+'/menu.nrq');let streams=[];
for(const [off,len] of [[144,3200],[3344,800],[5168,1200]]) {
 const raw=menu.subarray(off,off+len), packed=packBroadsideLzss(raw);
 if(!unpackBroadsideLzss(packed).equals(raw))throw Error('cache roundtrip');streams.push(packed);
}
fs.writeFileSync(out+'/menu-cache.bin',Buffer.concat(streams));
fs.writeFileSync(out+'/menu-cache.json',JSON.stringify(streams.map(s=>s.length)));
'''
    subprocess.run(['node','--input-type=module','-e',js,str(out),str(audio)],check=True)
    cache=(out/'menu-cache.bin').read_bytes();assert len(cache)<=1024
    p=c.blank(320,192)
    for y,row in enumerate(c.title_pixels()):p[y+8]=row[:]
    image=c.mono_image()
    for y in range(80):
        for x in range(320):p[48+y][x]=(image[y*40+x//8]>>(7-x%8))&1
    # Preserve menu illustration at native resolution; industrial framing.
    for y in [36,140]:c.line(p,24,y,295,y,1)
    for x in [24,295]:c.line(p,x,36,x,140,1)
    footer=c.footer_pixels()
    for y,row in enumerate(footer):p[157+y]=row[:]
    bitmap=bytearray()
    for y,row in enumerate(p):
        if y<157:bitmap.extend(sum(row[x+i]<<(7-i) for i in range(8)) for x in range(0,320,8))
        else:bitmap.extend(sum(row[x+2*i]<<(6-2*i) for i in range(4)) for x in range(0,320,8))
    dl=bytearray([0x70]*3)
    for y in range(192):
        mode=15 if y<157 else 14
        if y in [39,156]:mode|=128
        if y in [0,102]:dl.extend([mode|64]+list(struct.pack('<H',0xa010+y*40)))
        else:dl.append(mode)
    dl.extend([0x41,0,0x88]);assert len(dl)==202
    (out/'splash-pixels.json').write_text(json.dumps(p))
    (out/'splash-data.h').write_text('#define CACHE_BYTES '+str(len(cache))+'\n')
    (out/'splash-data.inc').write_text('CACHE_BYTES='+str(len(cache))+'\n')
    return c.package('splash',[(0xa010,bytes(bitmap)),(0x9000,cache),(0x8800,bytes(dl))],6)
