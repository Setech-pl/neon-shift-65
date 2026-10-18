#!/usr/bin/env python3
"""Deliver five verified HWVIS1 images; never overwrite an owner's play disk."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWNER=ROOT/'build/owner-smoke/hwvis1'
def sha(data):return hashlib.sha256(data).hexdigest()
def binding():return json.loads((ROOT/'docs/hwvis1/candidate.json').read_text())
def main():
    b=binding();OWNER.mkdir(parents=True,exist_ok=True)
    for n in (0,1,16,31,46):
        item=b['images'][str(n)];dest=OWNER/item['file']
        if dest.exists():assert sha(dest.read_bytes())==item['sha256'],f'Preserving different owner bytes: {dest}'
        else:
            src=ROOT/item['build']/'candidate.atr'
            if not src.exists():
                out=OWNER/f'recovery-{n}'
                cmd=[sys.executable,str(ROOT/'tools/v1_build.py'),'--out',str(out)]
                if n:cmd+=['--test-start',str(n)]
                subprocess.run(cmd,cwd=ROOT,check=True);src=out/'candidate.atr'
            data=src.read_bytes();assert sha(data)==item['sha256'];assert data[16+8099*128:16+8101*128]==bytes(256)
            dest.write_bytes(data)
    sums=''.join(f"{v['sha256']}  {v['file']}\n" for v in b['images'].values())
    (OWNER/'SHA256SUMS').write_text(sums)
    (OWNER/'START-HERE.txt').write_text((ROOT/'docs/hwvis1/HARDWARE-SMOKE.md').read_text())
    with zipfile.ZipFile(OWNER/'neon-shift65-hwvis1-owner.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted([item['file'] for item in b['images'].values()]+['SHA256SUMS','START-HERE.txt']):
            i=zipfile.ZipInfo(name,date_time=(2026,10,18,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,(OWNER/name).read_bytes())
    archive=OWNER/'neon-shift65-hwvis1-owner.zip'
    (OWNER/'SHA256SUMS').write_text(sums+f'{sha(archive.read_bytes())}  {archive.name}\n')
    print(OWNER)
if __name__=='__main__':main()
