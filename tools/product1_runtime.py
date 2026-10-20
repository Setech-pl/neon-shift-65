"""Build adapters for the single frozen engine; board/save data live on ATR."""
import hashlib,json,os,shutil,struct,subprocess,sys
from pathlib import Path
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'tools'))
from warehouses import crc16
from atr import offset
from product1_data import load

def prepare(out,source):
    campaign,levels=load();digest=bytes.fromhex(json.loads(campaign)['id'])
    (out/'campaign-id.h').write_text('static const unsigned char campaign_id[4]={'+','.join(map(str,digest))+'};\n')
    if os.environ.get('NEON_FINISH2_START','0')!='0':
        identity=hashlib.sha256(b'FINISH2 hardware test '+os.environ['NEON_FINISH2_START'].encode()+campaign).digest()[:4]
        with (out/'campaign-id.h').open('a') as f:
            f.write('static const unsigned char save_id[4]={'+','.join(map(str,identity))+'};\n')
    assets=out/'assets.c';shutil.copyfile(assets,out/'fixture-assets.c')
    text=assets.read_text();begin=text.index('#ifdef __ATARI__');assets.write_text('#include "level.h"\n'+text[begin:])
    for area in range(1,5):
        dest=out/f'art-area-{area}';dest.mkdir();shutil.copytree(out/'reference',dest/'reference')
        env=dict(os.environ,NEON_ART2_BUILD=str(dest),NEON_ART2_AREA=str(area))
        subprocess.run([sys.executable,str(ROOT/'tools/product1_art.py'),str(source)],env=env,check=True)

def pack(image,out):
    campaign,levels=load()
    digest=bytes.fromhex(json.loads(campaign)['id'])
    # Production has exactly 60 disk levels. Remove unreachable inherited
    # qualification packs (including First Dock), preserving menu/music slots.
    image[offset(512,128):offset(896,128)]=bytes((896-512)*128)
    directory=bytearray(image[offset(4,128):offset(4,128)+128])
    struct.pack_into('<H',directory,18,1101)
    if os.environ.get('NEON_PMG_INDUSTRIAL1')=='1':
        struct.pack_into('<HH',directory,20,48,6080)
    elif os.environ.get('NEON_PMG1')=='1':
        struct.pack_into('<HH',directory,20,48,6080)
    directory[32:64]=bytes(32)
    struct.pack_into('<H',directory,126,crc16(directory[:126]))
    image[offset(4,128):offset(4,128)+128]=directory
    catalog=bytearray(128);catalog[:6]=b'NSCD'+bytes([1,len(levels)]);catalog[8:12]=digest
    struct.pack_into('<H',catalog,126,crc16(catalog[:126]));image[offset(1000,128):offset(1000,128)+128]=catalog
    for i,l in enumerate(levels):
        board=bytearray(128);board[:8]=b'NSLV'+bytes([1,i,l['area'],sum(c in '$*' for r in l['rows'] for c in r)])
        player=next((x,y) for y,r in enumerate(l['rows']) for x,c in enumerate(r) if c in '@+')
        board[8:12]=bytes([*player,16,8]);board[12:16]=digest
        boxes=[]
        for y,row in enumerate(l['rows']):
            for x,c in enumerate(row):
                n=y*16+x;t=0 if c=='#' else 2 if c in '.*+' else 1
                board[16+n//4]|=t<<((n&3)*2)
                if c in '$*':boxes.extend([x,y])
        board[48:48+len(boxes)]=bytes(boxes);name=l['name'].encode('ascii');board[68:68+len(name)]=name
        struct.pack_into('<H',board,126,crc16(board[:126]))
        asset=(out/f"art-area-{l['area']}/level-{i+1:02d}/scene-0.nrq").read_bytes()
        if os.environ.get('NEON_PMG_INDUSTRIAL1')=='1':
            from pmg_industrial1_art import bind_overlay
            asset=bind_overlay(asset,(out/'renderer.bin').read_bytes())
        elif os.environ.get('NEON_PMG1')=='1':
            from pmg1_art import bind_overlay
            asset=bind_overlay(asset,(out/'renderer.bin').read_bytes())
        else:assert len(asset)==8768
        sector=1100+i*70;at=offset(sector,128)
        image[at:at+128]=board;image[at+128:at+128+len(asset)]=asset
