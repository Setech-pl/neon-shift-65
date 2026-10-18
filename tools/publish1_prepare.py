#!/usr/bin/env python3
"""Recover clean release media from the product commit; locked-source fallback for exports."""
import argparse, hashlib, json, subprocess, zipfile, tempfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRODUCT='600d934310b5ffb8e3fbf73a205f15a589a4efa6'
HASHES={0:'fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82',1:'a52bbcd758d408b711250d93b0cd92c90fb7e32529f45cb37cad2394ff5ff676',16:'b1f0495504e26aa836115a460b37760f41e18fab4ef386f87f174fe14a88e1ae',31:'44c24ec48f436e4f40bb2bb972f983a2057d8dfc73c3694fa68a468cd45d25dd',46:'956f51e462b4bd8ce65ffbf60f0194ff650400046962a35945b333f703724aec'}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(path):return subprocess.check_output(['git','show',PRODUCT+':'+path],cwd=ROOT,stderr=subprocess.DEVNULL)
def clean(n):
    old='neon-shift65-v1.0-'+(f'test-{n:02}' if n else 'candidate')+'.atr'
    try:data=blob('docs/release1/'+old)
    except subprocess.CalledProcessError:
        # A reviewed source export may preserve checkpoint identity without its
        # multi-GiB Git evidence history. Recover normal bytes from dist, and
        # rebuild test variants from locked source inputs in a fresh directory.
        normal=ROOT/'dist/neon-shift65-v1.0.0.atr'
        if not n and normal.is_file():data=normal.read_bytes()
        else:
            base=ROOT/'build/owner-smoke/recovery';base.mkdir(parents=True,exist_ok=True)
            session=Path(tempfile.mkdtemp(prefix='source-',dir=base));tree=session/'tree'
            subprocess.run([sys.executable,str(ROOT/'tools/publish1_sources.py'),'--out',str(tree)],check=True)
            cmd=[sys.executable,str(tree/'tools/v1_build.py'),'--out','build/variant']
            if n:cmd+=['--test-start',str(n)]
            subprocess.run(cmd,cwd=tree,check=True)
            data=(tree/'build/variant/candidate.atr').read_bytes()
    assert sha(data)==HASHES[n]
    assert data[16+8099*128:16+8101*128]==bytes(256),'Player save in source image'
    return data

def write_clean(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=data:
        raise SystemExit(f'Refusing to overwrite different bytes (possible private save): {path}')
    path.write_bytes(data)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--routes',action='store_true');a=p.parse_args()
    owner=ROOT/'build/owner-smoke';owner.mkdir(parents=True,exist_ok=True)
    files={}
    for n in HASHES:
        dest=ROOT/'dist/neon-shift65-v1.0.0.atr' if not n else owner/f'neon-shift65-v1.0.0-test-{n:02}.atr'
        data=dest.read_bytes() if dest.exists() and sha(dest.read_bytes())==HASHES[n] else clean(n)
        write_clean(dest,data);files[n]=dest
    manifest={'product_commit':PRODUCT,'images':[{'start':n or 'menu','file':str(f.relative_to(ROOT)),'sha256':HASHES[n]} for n,f in files.items()]}
    (owner/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(owner/'neon-shift65-v1.0.0-owner-smoke.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in files.values():z.writestr(f.name,f.read_bytes())
        z.writestr('manifest.json',json.dumps(manifest,indent=2))
        for name in ('docs/owner-smoke.md','docs/owner-smoke.pl.md'):
            if (ROOT/name).exists():z.writestr(Path(name).name,(ROOT/name).read_bytes())
    if a.routes:
        from release1_owner_smoke import route_disk
        records=[route_disk(n,files[0],owner/f'routes/smoke-level-{n:02}.atr') for n in (15,30,45,60)]
        for r in records:r['path']=str(Path(r['path']).relative_to(ROOT))
        (owner/'routes/routes.json').write_text(json.dumps(records,indent=2)+'\n')
    print('PASS: five clean images from '+PRODUCT+'; private play copies retained')
if __name__=='__main__':main()
