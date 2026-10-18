#!/usr/bin/env python3
"""Focused verification of PUBLISH1 packaging, links and unretouched media."""
import hashlib,json,re,subprocess,zipfile
from pathlib import Path
from publish1_prepare import ROOT,HASHES,PRODUCT,sha

def raw_hash(args):
    p=subprocess.Popen(['ffmpeg','-v','error',*map(str,args),'-pix_fmt','rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE)
    h=hashlib.sha256()
    while True:
        data=p.stdout.read(1024*1024)
        if not data:break
        h.update(data)
    assert p.wait()==0
    return h.hexdigest()

def main(workdir='build/owner-smoke/media', reportdir='docs/publish1', freshbuild='build/publish1-fresh-source/build/normal/candidate.atr', current=False):
    atr=ROOT/'dist/neon-shift65-v1.0.0.atr';assert sha(atr.read_bytes())==HASHES[0]
    z=zipfile.ZipFile(ROOT/'dist/neon-shift65-v1.0.0.zip');assert z.read(atr.name)==atr.read_bytes()
    for line in (ROOT/'dist/SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ');assert sha((ROOT/'dist'/name).read_bytes())==expected,name
    docs=[ROOT/'README.md',ROOT/'README.pl.md',ROOT/'docs/README.md',ROOT/'docs/building.md']
    docs+=list((ROOT/'docs').glob('how-to-play*.md'))+list((ROOT/'docs').glob('quick-start*.md'))+list((ROOT/'docs').glob('release-notes*.md'))+list((ROOT/'docs').glob('credits*.md'))+list((ROOT/'docs').glob('owner-smoke*.md'))+list((ROOT/'docs/media').glob('README*.md'))
    links=0
    for p in docs:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if link.startswith(('https:','http:','#')):continue
            target=link.split('#')[0];assert (p.parent/target).exists(),(p,link);links+=1
    pairs=[(ROOT/'README.md',ROOT/'README.pl.md')]+[(ROOT/'docs'/f'{n}.md',ROOT/'docs'/f'{n}.pl.md') for n in ('how-to-play','quick-start','release-notes','credits','owner-smoke')]+[(ROOT/'docs/media/README.md',ROOT/'docs/media/README.pl.md')]
    for en,pl in pairs:
        assert pl.name in en.read_text().splitlines()[0] and en.name in pl.read_text().splitlines()[0]
        if en.name=='README.md' and en.parent==ROOT:
            assert re.findall(r'!\[.*?\]\(([^)]+)\)',en.read_text())==re.findall(r'!\[.*?\]\(([^)]+)\)',pl.read_text())
    media=ROOT/'docs/media';work=ROOT/workdir;proof=[]
    for n in (1,2,3,4):
        reference=raw_hash(['-framerate','10','-i',work/f'area-{n}/clip-%03d.png','-vf','scale=iw*2:ih*2:flags=neighbor'])
        decoded=raw_hash(['-i',media/f'area-{n}.gif','-fps_mode','passthrough'])
        assert reference==decoded,('GIF changed pixels',n)
        raw=(media/f'area-{n}.gif').read_bytes();assert b'NETSCAPE2.0\x03\x01\x00\x00' in raw
        metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-show_entries','stream=width,height,nb_frames','-of','json',str(media/f'area-{n}.gif')]))
        assert abs(float(metadata['format']['duration'])-4.01117)<0.02
        proof.append({'area':n,'decoded_rgb_sha256':decoded,'exact_nearest_neighbour_pixels':True,'duration':metadata['format']['duration'],'infinite_loop':True})
    assert raw_hash(['-i',media/'neon-shift65.gif','-fps_mode','passthrough'])==raw_hash(['-framerate','10','-i',work/'montage-%03d.png','-vf','scale=iw*2:ih*2:flags=neighbor'])
    manifest=json.loads((media/'manifest.json').read_text())
    for record in manifest['runs']:
        for name,f in record['screenshots'].items():
            assert raw_hash(['-i',work/f"area-{record['area']}/native-{f:04}.png",'-vf','scale=iw*2:ih*2:flags=neighbor'])==raw_hash(['-i',media/(name+'.png')]),name
    result={'status':'PASS','product_commit':PRODUCT,'normal_atr_sha256':HASHES[0],'zip_atr_identical':True,'checksums':True,'current_document_local_links':links,'bilingual_pairs':len(pairs),'readme_images_same_order':True,'visual_review':'All six PNGs and selected motion/undo/cut/loop frames of all five GIFs inspected; uncropped 336x240 native frames, 2x NN; no colour or object edits','gif_rgb_proofs':proof,'main_gif_exact_rgb':True,'six_png_exact_rgb':True,'hardware':'OWNER_PENDING','rights':'OPEN','remote_draft':'Not created: target commit absent from empty remote; independent initial export awaiting owner decision'}
    if current:
        result['remote_draft']='See publication.json; private candidate, no stable publication.'
        result['visual_review']='Current menu, loader, four area PNGs inspected; exact RGB checks on every GIF/PNG and montage. Hardware OWNER_PENDING.'
    recovery=ROOT/reportdir/'source-recovery.json'
    if recovery.exists():result['source_snapshot_recovery']=json.loads(recovery.read_text())
    fresh=ROOT/freshbuild
    if fresh.exists():
        assert sha(fresh.read_bytes())==HASHES[0]
        result['fresh_normal_rebuild_sha256']=HASHES[0]
    (ROOT/reportdir/'publication-verification.json' if current else ROOT/'docs/publish1/verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
