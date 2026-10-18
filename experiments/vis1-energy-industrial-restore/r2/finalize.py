"""Freeze limited r2 evidence and run only the owner's --check launcher."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BUILD=ROOT/'build/vis1-energy-industrial-restore/r2'
DOCS=ROOT/'docs/checkpoints/vis1-energy-industrial-restore/r2'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source=json.loads((BUILD/'area-1/source-manifest.json').read_text())
    verification=json.loads((BUILD/'verification.json').read_text())
    assert source['ATR_sha256']==verification['ATR_sha256']
    for name,digest in {**source['actually_used_sources'],**source['generated_build_inputs']}.items():
        assert sha(ROOT/name)==digest,(name,'source binding')
    protected=json.loads((DOCS/'preflight.json').read_text())
    changed=[name for name,digest in protected['files'].items()
             if not (ROOT/name).is_file() or sha(ROOT/name)!=digest]
    cfg=Path.home()/'.atari800.cfg'
    home_digest=sha(cfg) if cfg.exists() else None
    assert not changed and home_digest==protected['home_config_sha256']
    (DOCS/'preservation.json').write_text(json.dumps(dict(status='PASS',
        checked_files=len(protected['files']),changed_files=changed,
        home_config_sha256=home_digest,home_config_unchanged=True,
        previous_VIS1_preserved=True,other_projects='No writes or commands in Void Strike'),indent=2)+'\n')
    with zipfile.ZipFile(DOCS/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
        names=set(source['actually_used_sources'])|set(source['generated_build_inputs'])
        names.update(str(p.relative_to(ROOT)) for p in HERE.glob('*.py'))
        names.add('docs/lessons-learned-visual-drift.md')
        for name in sorted(names):z.write(ROOT/name,name)
    with zipfile.ZipFile(DOCS/'evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        files=list((BUILD/'captures').rglob('*'))+list((BUILD/'baseline').rglob('*'))
        files+=list(BUILD.glob('*.log'))
        for f in sorted(files):
            if f.is_file():z.write(f,str(f.relative_to(BUILD)))
    # Also bind cross-area controls to their actual, current source manifests.
    for a in (2,3,4):
        dest=DOCS/'area-controls'/f'area-{a}';dest.mkdir(parents=True,exist_ok=True)
        for name in ('source-manifest.json','candidate-atr.json'):
            shutil.copyfile(BUILD/f'area-{a}'/name,dest/name)
        shutil.copyfile(BUILD/f'area-{a}-build.log',dest/'build.log')
    previous=json.loads((DOCS.parent/'manifest.json').read_text())
    for entry in previous['toolchain'].values():
        assert sha(Path(entry['path']))==entry['sha256'],'Toolchain changed'
    observer=ROOT/previous['emulator']['path']
    assert sha(observer)==previous['emulator']['sha256']
    record=dict(stage='VIS1-r2',base_commit=protected['head'],branch=protected['branch'],
        source_commit_resolution='git log -1 --format=%H -- docs/checkpoints/vis1-energy-industrial-restore/r2/manifest.json',
        source_commit_note='Exact new local commit also in ZIP delivery.json, written after the commit to avoid circular hashing',
        owner_visual='OWNER NOT_RUN',engine_status='ENGINE FAIL (historical; not requalified)',
        contract='ENG3-B-v1',build='python3 experiments/vis1-energy-industrial-restore/r2/build.py',
        configuration=source['configuration'],candidate_ATR_sha256=verification['ATR_sha256'],
        baseline_commit=protected['head'],baseline_ATR_sha256=verification['baseline_ATR_sha256'],
        actual_sources=source['actually_used_sources'],generated_inputs=source['generated_build_inputs'],
        evidence_scripts={str(p.relative_to(ROOT)):sha(p) for p in sorted(HERE.glob('*.py'))},
        toolchain=previous['toolchain'],emulator=previous['emulator'],
        owner_command='python3 experiments/vis1-energy-industrial-restore/r2/owner_smoke.py',
        lessons_learned=dict(path='docs/lessons-learned-visual-drift.md',
                            sha256=sha(ROOT/'docs/lessons-learned-visual-drift.md')),
        memory=verification['memory'])
    (DOCS/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    result=subprocess.run([sys.executable,str(HERE/'owner_smoke.py'),'--check'],
                          capture_output=True,text=True,check=True)
    (DOCS/'owner-smoke/launch-check.json').write_text(result.stdout)
    launch=json.loads(result.stdout)
    assert launch['display_mode']=='WINDOWED' and not launch['config_autosave']
    assert launch['ATR_sha256']==record['candidate_ATR_sha256']
    record['files']={str(p.relative_to(DOCS)):sha(p) for p in sorted(DOCS.rglob('*'))
                     if p.is_file() and p.name!='manifest.json'}
    (DOCS/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    import package
    package.archive()
    print('PASS source binding, preservation, owner --check, manifest and ZIP')


if __name__=='__main__':main()
