#!/usr/bin/env python3
"""Owner evidence: unchanged native frames, exact replication/crops, outer labels.

No tiles are rendered or artwork retouched. Every image cites its real ATR frame.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'build/vis1-energy-industrial-restore'
DOCS=ROOT/'docs/checkpoints/vis1-energy-industrial-restore'
sys.path.insert(0,str(ROOT/'experiments/eng3-observed-input-3pal'))
from native_image import Image,ImageDraw


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def zoom(im,n):
    return Image(np.repeat(np.repeat(im.pixels,n,axis=0),n,axis=1))


def caption(im,x,y,text):
    ImageDraw.Draw(im).text((x,y),text)


def main():
    DOCS.mkdir(parents=True,exist_ok=True)
    for d in ('native/baseline','native/candidate','zoom3x/baseline','zoom3x/candidate',
              'comparisons','details/baseline','details/candidate','owner-smoke'):
        (DOCS/d).mkdir(parents=True,exist_ok=True)
    records=[]
    states=[('01-start-16x8',950,'START 16X8 / 00 STEPS / 00 PUSH / 00-04 DOCKS'),
        ('02-docked-16x8',1220,'RLDRDDLLURURUR / 14 STEPS / 04 PUSH / 01-04 DOCKS'),
        ('03-replay69',2120,'REPLAY69 / 69 STEPS / 11 PUSH / 04-04 DOCKS'),
        ('04-max-20x10',3340,'MAX 20X10 / EXISTING 09-10 DOCK FIXTURE'),
        ('05-small-6x3',3780,'SMALL 6X3 / 00 STEPS / 00 PUSH / 00-01 DOCKS')]
    for name,frame,title in states:
        canvas=Image.new('RGB',(2032,760))
        for i,variant in enumerate(('baseline','candidate')):
            run=BUILD/'captures'/f'{variant}-review'
            source=run/f'native-{frame:04}.png'
            native=DOCS/'native'/variant/f'{name}.png'
            enlarged=DOCS/'zoom3x'/variant/f'{name}.png'
            shutil.copyfile(source,native)
            im=Image.open(source)
            assert im.pixels.shape==(240,336,3)
            z=zoom(im,3);z.save(enlarged)
            assert np.array_equal(Image.open(enlarged).pixels,z.pixels)
            x=i*1024
            caption(canvas,x+8,6,variant.upper()+' / FRAME '+str(frame))
            caption(canvas,x+8,22,title)
            canvas.paste(z,(x,40))
            actual=json.loads((run/'states.json').read_text())[str(frame)]
            records.append(dict(file=str(native.relative_to(DOCS)),zoom=str(enlarged.relative_to(DOCS)),
                source=str(source.relative_to(ROOT)),frame=frame,variant=variant,state=actual,
                native_SHA256=sha(native),zoom_SHA256=sha(enlarged),
                ATR_SHA256=json.loads((run/'artifact.json').read_text())['ATR']['sha256']))
        canvas.save(DOCS/'comparisons'/f'{name}.png')
    # All crops refer to actual native ATR pixels, including adjacent docked boxes.
    objects=[('ROBOT',950,5,3,1,0),('CONTAINER',950,6,3,1,0),
             ('EMPTY DOCK',950,8,3,1,0),('OCCUPIED DOCK',1220,8,3,1,0),
             ('ADJACENT DOCKED',3340,2,2,2,1)]
    detail=Image.new('RGB',(620,5*152))
    for i,(name,f,x,y,width,scene) in enumerate(objects):
        for j,variant in enumerate(('baseline','candidate')):
            source=BUILD/'captures'/f'{variant}-review'/f'native-{f:04}.png'
            bx,by=([4,5] if scene==0 else [0,3])
            xx=8+(bx+2*x)*8;yy=24+(by+2*y)*8
            cropped=Image.open(source).crop((xx,yy,xx+width*16,yy+16))
            filename=name.lower().replace(' ','-')+'.png'
            target=DOCS/'details'/variant/filename
            cropped.save(target)
            caption(detail,j*310+4,i*152+4,variant.upper()+' / '+name)
            detail.paste(zoom(cropped,8),(j*310+4,i*152+20))
            records.append(dict(file=str(target.relative_to(DOCS)),source=str(source.relative_to(ROOT)),
                frame=f,variant=variant,crop=[xx,yy,xx+width*16,yy+16],native_SHA256=sha(target)))
    detail.save(DOCS/'details-before-after.png')
    (DOCS/'screens.json').write_text(json.dumps(records,indent=2)+'\n')
    shutil.copyfile(BUILD/'area-1/candidate.atr',DOCS/'owner-smoke/neon-shift65-vis1-energy.atr')
    for name in ('candidate.map','candidate.lbl','candidate-atr.json','source-manifest.json'):
        shutil.copyfile(BUILD/'area-1'/name,DOCS/name)
    # Preserve the original linker map in build; archive its whitespace-clean
    # text so the checkpoint passes git diff --check without changing addresses.
    map_path=DOCS/'candidate.map'
    map_path.write_text('\n'.join(line.rstrip() for line in map_path.read_text().splitlines()).rstrip()+'\n')
    shutil.copyfile(BUILD/'verification.json',DOCS/'verification.json')
    shutil.copyfile(ROOT/'build/visual-baseline/capture-base.cfg',DOCS/'capture-base.cfg')
    shutil.copyfile(BUILD/'captures/candidate-review/emulator.cfg',DOCS/'headless-capture.cfg')
    for name in ('build.log','verify.log'):
        shutil.copyfile(BUILD/name,DOCS/name)
    # Existing ffmpeg makes a 101-frame actual push/undo film, with exact palette.
    ffmpeg=shutil.which('ffmpeg')
    if ffmpeg:
        colours=np.unique(np.concatenate([np.unique(Image.open(
            BUILD/f'captures/candidate-response/native-{f:04}.png').pixels.reshape(-1,3),axis=0)
            for f in range(990,1091)]),axis=0)
        assert len(colours)<=256
        palette=np.zeros((256,3),dtype=np.uint8)
        palette[:len(colours)]=colours
        palette[len(colours):]=colours[0]
        # A literal palette avoids palettegen's perceptual RGB rounding.
        palette_path=BUILD/'gif-palette.png'
        Image(palette.reshape(16,16,3)).save(palette_path)
        subprocess.run([ffmpeg,'-y','-v','error','-framerate','50','-start_number','990',
            '-i',str(BUILD/'captures/candidate-response/native-%04d.png'),
            '-i',str(palette_path),
            '-frames:v','101','-filter_complex',
            '[0:v]format=rgb24,scale=1008:720:flags=neighbor,format=rgb24[v];[v][1:v]paletteuse=dither=none',
            str(DOCS/'animations-push-undo.gif')],check=True)
    print('Packaged native frames, exact3x comparisons and native8x crops:',len(records))


def archive():
    # Called after the report/manifest have been written and owner --check passed.
    path=BUILD/'neon-shift65-vis1-energy-industrial-restore.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(DOCS.rglob('*')):
            if f.is_file():
                z.write(f,'vis1-energy-industrial-restore/'+str(f.relative_to(DOCS)))
        for f in sorted(Path(__file__).parent.glob('*.py')):
            z.write(f,'vis1-energy-industrial-restore/source/'+f.name)
        z.write(ROOT/'reference/vis1-owner/energy-owner-reference.png',
                'vis1-energy-industrial-restore/energy-owner-reference.png')
    print(path,sha(path))
    return path


if __name__=='__main__':
    main()
