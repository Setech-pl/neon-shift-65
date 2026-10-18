#!/usr/bin/env python3
"""Seal one RC1 ATR, actual build inputs, captures, preservation and hashes."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/finish1'
BUILD=ROOT/'build/finish1/rc1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main():
    evidence=DOC/'evidence';evidence.mkdir(exist_ok=True)
    for p in (BUILD/'build.log',BUILD/'v1-binding.json',BUILD/'campaign-full/campaign-result.json',BUILD/'campaign-full/timing.json'):
        shutil.copyfile(p,evidence/p.name)
    for name in ('candidate.map','candidate.lbl'):
        raw=(BUILD/name).read_text();normalized='\n'.join(x.rstrip() for x in raw.splitlines()).rstrip()+'\n'
        assert raw.split()==normalized.split();(evidence/name).write_text(normalized)
    for name in ('launch.json','emulator.cfg'):
        shutil.copyfile(ROOT/'build/finish1/owner-smoke'/name,evidence/('owner-'+name))
    before=json.loads((ROOT/'docs/art-final/manifest.json').read_text())
    sources={ROOT/p for p in before['source_dependency_inventory']}
    sources.update((ROOT/'tools').glob('finish1_*.py'))
    sources.add(ROOT/'tools/camp2b_campaign.py')
    sources.add(ROOT/'experiments/finish1/art.py')
    sources.add(ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg')
    generated=set()
    for build in (BUILD,ROOT/'build/finish1/rebuild-proof'):
        generated.update(p for p in (build/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.o'))
        generated.update((build/'cc-input').glob('*.c'))
        generated.update(p for p in build.iterdir() if p.is_file() and p.suffix in ('.c','.h','.s','.inc','.cfg'))
        for area in range(1,5):
            for pattern in ('level-*/scene-0.nrq','level-*/scene-0-banks.json'):
                generated.update((build/f'art-area-{area}').glob(pattern))
    with zipfile.ZipFile(DOC/'source-inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(sources|generated):z.write(p,str(p.relative_to(ROOT)))
    raw=set();run=BUILD/'campaign-full'
    runs={run}
    for t in json.loads((DOC/'save-results.json').read_text())['tests']:runs.add(Path(t['out']))
    selected=('artifact.json','command.json','emulator.cfg','host-pacing.json','timing.json','routine-timing.json','trace-symbols.json')
    for r in runs:
        for p in r.iterdir():
            if p.is_file() and (p.suffix in ('.ram','.png','.gz') or p.name in selected):raw.add(p.resolve())
    # Baseline comparison evidence already existed; archive only the compared
    # frames here, with all original hashes and no repeated baseline replay.
    prior=ROOT/'build/art-final/final/campaign-full'
    for r in json.loads((DOC/'screenshots.json').read_text())['records']:
        for prefix,suffix in (('frame','.ram'),('raster','.ram'),('native','.png')):
            raw.add(prior/f"{prefix}-{r['initial_frame']:04}{suffix}")
    for name in selected:
        p=prior/name
        if p.exists():raw.add(p)
    for p in (ROOT/'build/finish1/save-media').glob('*.atr'):raw.add(p)
    captures={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(raw)}
    with zipfile.ZipFile(DOC/'capture-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(raw):z.write(p,str(p.relative_to(ROOT)))
    dump(DOC/'capture-manifest.json',captures)
    pre=json.loads((DOC/'preflight.json').read_text());v=json.loads((DOC/'verification.json').read_text())
    atr=DOC/'owner-smoke/neon-shift65-v1.0-RC1.atr'
    assert atr.read_bytes()==(BUILD/'candidate.atr').read_bytes()
    assert all(sha(ROOT/p)==h for p,h in pre['preserved_files'].items())
    assert sha(Path.home()/'.atari800.cfg')==pre['owner_config_sha256']
    manifest=dict(base_commit=pre['HEAD_before'],branch=pre['branch'],candidate='NEON SHIFT 65 v1.0-RC1 / FINISH1',
        ATR=str(atr.relative_to(ROOT)),ATR_sha256=sha(atr),ATR_bytes=atr.stat().st_size,
        campaign=dict(path='assets/levels/camp2-b/campaign.json',sha256=pre['campaign_sha256'],ID='131c57e2',levels=60,bytes_unchanged=True),
        build='python3 tools/v1_build.py --out <fresh-directory>',
        reproducibility='build/finish1/rebuild-proof: fresh build from final source hooks produces byte-identical ATR',
        source_dependency_inventory={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},
        generated_input_and_NRQs={str(p.relative_to(ROOT)):sha(p) for p in sorted(generated)},
        archives={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in (DOC/'source-inputs.zip',DOC/'capture-evidence.zip')},
        capture=dict(observer='build/eng3-observed-input-3pal/observer/src/atari800',observer_sha256=sha(ROOT/'build/eng3-observed-input-3pal/observer/src/atari800'),
            config='docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg',config_sha256=sha(ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg'),
            mode='SDL dummy headless only; owner launcher --check only',baseline='Existing f5df646 full campaign native captures; identical inputs, config, frame and logical state'),
        art_origin=dict(composition='Documented VIS1-r2 / frozen scene-map vocabulary, recovered in 99cc101',
            objects='f5df646 ART-FINAL closed cargo, corner dock and ART4-A 40-state service robot, now all areas',
            machines='Existing Energy VIS1-r2 and Hydroponic/Data Hub/Reactor theme devices; identical placement and animation schedules',
            new='FINISH1 common bevel/plate/vent/service-trunk pixels and four material palettes; neutral ambient ink',
            boundary='No newly identified owner native PNG; October12 source attribution remains bounded by RECOVERY1 report'),
        evidence=dict(verification_sha256=sha(DOC/'verification.json'),save_results_sha256=sha(DOC/'save-results.json'),
            before_report='docs/art-final/REPORT.md',before_manifest_sha256=sha(ROOT/'docs/art-final/manifest.json'),
            original_native_undo_and_ENG4_reused='Exact unchanged instructions/maps; new full60 art replay and six RC1 save/redraw probes'),
        preservation=dict(previous_art_final_and_recovery_files=len(pre['preserved_files']),all_unchanged=True,owner_config_unchanged=True),
        owner_acceptance=pre['owner_acceptance'],RC1_visual_owner='PENDING',hardware='NOT_RUN',published=False)
    dump(DOC/'manifest.json',manifest)
    paths=[p for p in DOC.rglob('*') if p.is_file() and p.name!='SHA256SUMS']
    (DOC/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DOC)}\n' for p in sorted(paths)))
    print('PASS RC1 sealed:',sha(atr),'capture files',len(raw))

if __name__=='__main__':main()
