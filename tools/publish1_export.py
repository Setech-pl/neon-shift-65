#!/usr/bin/env python3
"""Prepare a reviewable source snapshot; never create commits or push.
Local history/evidence remain untouched. A separate initial remote history needs
an explicit owner decision because the existing history cannot be safely pushed.
"""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from publish1_prepare import ROOT,PRODUCT,blob

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--refresh',action='store_true');a=p.parse_args()
    out=a.out.resolve()
    if a.refresh and out.exists():
        assert (out/'EXPORT-MANIFEST.json').is_file() and not (out/'.git').exists(),'Only refresh this tool’s uncommitted generated export'
        shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=False)
    lock=json.loads((ROOT/'docs/publish1/source-inputs.json').read_text())
    files={}
    for n,expected in lock['inputs'].items():
        try:data=blob(n)
        except subprocess.CalledProcessError:data=(ROOT/n).read_bytes()
        assert hashlib.sha256(data).hexdigest()==expected,n
        files[n]=data
    for n in ['.gitignore','README.md','README.pl.md','LICENSE','LICENSE-ASSETS','THIRD_PARTY_NOTICES.md','PLAY-WINDOWED.command','docs/README.md','docs/building.md','assets/graphics/mono-font-NOTICE.md','assets/licenses/void-strike-MIT.txt','assets/licenses/void-strike-LICENSE-ASSETS.md']:
        files[n]=(ROOT/n).read_bytes()
    for directory in ('dist','docs/media','docs/licenses','docs/publish1'):
        for f in (ROOT/directory).rglob('*'):
            if f.is_file():files[str(f.relative_to(ROOT))]=f.read_bytes()
    for f in (ROOT/'docs').glob('*.md'):
        if f.name in ['owner-smoke.md','owner-smoke.pl.md','how-to-play.md','how-to-play.pl.md','quick-start.md','quick-start.pl.md','release-notes.md','release-notes.pl.md','credits.md','credits.pl.md']:
            files[str(f.relative_to(ROOT))]=f.read_bytes()
    for f in (ROOT/'tools').glob('publish1_*.py'):files[str(f.relative_to(ROOT))]=f.read_bytes()
    files['tools/release1_owner_smoke.py']=(ROOT/'tools/release1_owner_smoke.py').read_bytes()
    # Only reports and small named evidence; never sweep unknown owner folders.
    for n in ('docs/release1/REPORT.md','docs/release1/HARDWARE-SMOKE.md','docs/release1/FREEZE.md','docs/independent-audit-claude/REPORT.md','docs/independent-rereview-600d934/REPORT.md','docs/architecture.md','PROJECT_BRIEF.md'):
        files[n]=(ROOT/n).read_bytes()
    # Build helpers copy this source tree. Preserve the actual observer source.
    for n in ('tools/emulator_trace.h',):files[n]=(ROOT/n).read_bytes()
    assert not any(Path(n).suffix.lower() in ('.rom','.car') or Path(n).name=='emulator.cfg' for n in files)
    assert not any(len(d)>=100*1024**2 for d in files.values())
    for n,data in files.items():
        target=out/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    manifest={'product_commit':PRODUCT,'role':'Reviewable proposed initial source snapshot, not pushed; local history and evidence preserved','files':{n:{'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)} for n,d in sorted(files.items())},'excluded':'All historical large evidence archives, private emulator configs, raw capture RAM, owner reference bitmap and untracked owner files. Historical report links to omitted raw evidence are archival, not online evidence claims.'}
    (out/'EXPORT-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'path':str(out),'files':len(files),'bytes':sum(map(len,files.values())),'largest':max((len(d),n) for n,d in files.items())},indent=2))
if __name__=='__main__':main()
