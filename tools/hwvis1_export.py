#!/usr/bin/env python3
"""Update prepared PUBLISH1 snapshot into a separate export, never source history."""
import argparse,hashlib,json,re,shutil,subprocess,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def scan(files):
    hits=[];bad=[]
    rules={'AWS access id':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b','GitHub token':rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b','Private key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----','OpenAI token':rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b'}
    def check(name,data):
        p=Path(name)
        if p.suffix.lower() in ('.rom','.car','.ram','.cfg') or p.name in ('.env','emulator.cfg') or any(n in ('.git','.aws','.ssh','.codex') for n in p.parts):bad.append(name)
        if len(data)>=100*1024**2:bad.append(name+' (100 MiB or more)')
        for label,pattern in rules.items():
            if re.search(pattern,data):hits.append(dict(file=name,rule=label))
        if p.suffix=='.zip':
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for member in z.infolist():
                    if not member.is_dir():check(name+'!/'+member.filename,z.read(member))
    for n,data in files.items():check(n,data)
    # .cfg files are linker/build inputs, allow ONLY the explicit compiler locks.
    allowed=set(json.loads((ROOT/'docs/hwvis1/source-inputs.json').read_text())['inputs'])
    bad=[n for n in bad if n not in allowed]
    assert not hits,{'secret_findings':hits} # Values are never logged.
    assert not bad,{'forbidden_paths':bad}
    return dict(status='PASS',secret_rules=list(rules),secret_findings=hits,forbidden_files=bad,archive_contents_checked=True,files=len(files),bytes=sum(map(len,files.values())),largest=sorted([dict(file=n,bytes=len(d)) for n,d in files.items()],key=lambda x:x['bytes'],reverse=True)[:5],limits='Pattern/inventory scan, not a proof that arbitrary encoded secrets cannot exist. No owner untracked sweep.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'build/publish2-export');a=p.parse_args();out=a.out.resolve()
    initial=ROOT/'build/publish1-reviewable-export';assert (initial/'EXPORT-MANIFEST.json').is_file();assert not (initial/'.git').exists()
    assert not out.exists(),'Use a new output; never rewrite an existing export repository'
    files={str(f.relative_to(initial)):f.read_bytes() for f in initial.rglob('*') if f.is_file()}
    for name in json.loads((ROOT/'docs/hwvis1/source-inputs.json').read_text())['inputs']:files[name]=(ROOT/name).read_bytes()
    # Refresh all previously selected current docs/resources, preserving selection.
    for name in list(files):
        if (ROOT/name).is_file() and name!='EXPORT-MANIFEST.json':files[name]=(ROOT/name).read_bytes()
    for folder in ('docs/hwvis1','dist','docs/media'):
        for f in (ROOT/folder).rglob('*'):
            if f.is_file():files[str(f.relative_to(ROOT))]=f.read_bytes()
    names=[str(f.relative_to(ROOT)) for f in (ROOT/'tools').glob('hwvis1*') if f.is_file()]
    names += ['tools/'+n for n in ('release1_runtime.py','release1_core.py','release1_fire.py','release1_faults.py','release1_routes.py','release1_extra.py','finish2_probe.py','product1_gauntlet.py','product1_fix1_review.py','product1_eng4.py','art_final_audit.py','recovery1_audit.py','finish2_audit.py','emulator_smoke.py')]
    names += ['docs/independent-audit-claude/repro/save-slots.bin']
    for name in names:files[name]=(ROOT/name).read_bytes()
    checkpoint=(ROOT/'docs/hwvis1/source-checkpoint.txt').read_text().strip()
    provenance=dict(source_checkpoint=checkpoint,source_branch='fix/hwvis1-publish2',previous_product_checkpoint='600d934310b5ffb8e3fbf73a205f15a589a4efa6',previous_packaging_checkpoint='154560ddd49f35d037e90d2141a363cd49306cb3',export_commit='Resolve git rev-parse HEAD in this independent repository; original workspace records actual mapping in docs/hwvis1/publication.json.',role='Independent initial export authorized by owner; original source repository/history/evidence preserved',normal_atr_sha256=sha(files['dist/neon-shift65-v1.0.0.atr']))
    files['EXPORT-PROVENANCE.json']=(json.dumps(provenance,indent=2)+'\n').encode()
    files.pop('EXPORT-MANIFEST.json',None)
    result=scan(files)
    for n,data in files.items():
        dest=out/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        if n=='PLAY-WINDOWED.command':dest.chmod(0o755)
    manifest=dict(source_checkpoint=checkpoint,role='HWVIS1/PUBLISH2 independent export; no original .git/history/private configuration',files={n:dict(sha256=sha(d),bytes=len(d)) for n,d in sorted(files.items())},scan=result,excluded='Historical large evidence and private configs, ROMs, owner reference bitmaps/untracked work, save disks, internal test ATRs. Some preserved historical reports link archival local-only evidence.')
    (out/'EXPORT-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'docs/hwvis1/export-scan.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(path=str(out),**result),indent=2))
if __name__=='__main__':main()
