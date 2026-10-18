#!/usr/bin/env python3
"""Seal the single ART-FINAL candidate and its source/capture provenance."""
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/art-final'
BUILD=BASE/'final'
DOC=ROOT/'docs/art-final'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)


def main():
    evidence=DOC/'evidence'
    for source,dest in ((BUILD/'campaign-full/campaign-result.json','campaign-result.json'),
                        (BUILD/'native-campaign/result.json','native-result.json'),
                        (BUILD/'native-campaign/replay.c','native-replay.c'),
                        (BUILD/'native-campaign/replay.log','native-replay.log'),
                        (BASE/'save-results.json','save-results.json'),
                        (BUILD/'eng4-art-final/eng4-result.json','eng4-result.json'),
                        (BUILD/'v1-binding.json','v1-binding.json'),(BUILD/'build.log','build.log')):
        copy(source,evidence/dest)
    for name in ('candidate.map','candidate.lbl'):
        raw=(BUILD/name).read_text();text='\n'.join(line.rstrip() for line in raw.splitlines()).rstrip()+'\n'
        assert raw.split()==text.split();(evidence/name).write_text(text)
    for f in ('launch.json','emulator.cfg'):copy(BASE/'owner-smoke'/f,evidence/'owner-smoke'/f)
    for v in ('before','final','bands'):copy(BASE/('captures-'+v+'.json'),evidence/('captures-'+v+'.json'))
    assert (DOC/'owner-smoke/neon-shift65-v1-art-final.atr').read_bytes()==(BUILD/'candidate.atr').read_bytes()
    sources=set()
    for directory in ('src','cfg','experiments/eng3-observed-input-3pal','experiments/product1','experiments/vis1-energy-industrial-restore','experiments/art4-a','experiments/art-final'):
        sources.update(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.o','.pyc','.zip','.png','.atr'))
    sources.update(ROOT.glob('tools/art_final_*.py'))
    for n in ('v1_build','product1_build','product1_runtime','product1_data','product1_art','assets','warehouses','atr','solver','scenes',
              'product1_gauntlet','product1_eng4','product1_fix1_review','product1_campaign','product1_owner_smoke','camp2b_campaign','camp2_solver',
              'emulator_smoke','m1_check','recovery1_audit','recovery1_visuals'):
        sources.add(ROOT/f'tools/{n}.py')
    for n in ('gauntlet','verify','pixel_fast','turbo_run','fetch_oracle'):
        p=ROOT/f'experiments/renderer-a5c/{n}.py'
        if p.exists():sources.add(p)
    sources.add(ROOT/'experiments/art3-contextual-decoration-review/floor_restore.py')
    for n in ('assets/levels/camp2-b/campaign.json','assets/levels/prototypes.json','assets/graphics/mono-font.json','assets/graphics/pal-palette.json','README.md'):
        sources.add(ROOT/n)
    generated=set()
    for build in (BUILD,BASE/'bands-prototype'):
        generated.update(p for p in (build/'source').iterdir() if p.is_file() and p.suffix in ('.py','.c','.s','.h','.cfg','.json'))
        generated.update((build/'cc-input').glob('*.c'))
        for name in ('level.c','game.c','undo.c','assets.c','aliases.s','numfont.s','campaign-id.h','neon-palette.h','neon-palette.inc',
                     'splash-data.h','splash-data.inc','boot-splash.inc','early-support.s','early-splash.s','early.cfg','early-text.cfg','prototype_assets.h'):
            p=build/name
            if p.exists():generated.add(p)
        for area in range(1,5):
            for pattern in ('level-*/scene-0.nrq','level-*/scene-0-banks.json'):
                generated.update((build/f'art-area-{area}').glob(pattern))
    generated.update((BUILD/'native-campaign/replay.c',BASE/'eng4-adapter.py',BASE/'eng4-pins.json'))
    with zipfile.ZipFile(DOC/'source-inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(sources|generated):z.write(p,str(p.relative_to(ROOT)))
    runs={BUILD/'campaign-full',BUILD/'eng4-art-final'}
    for v in ('before','final','bands'):
        for record in json.loads((BASE/('captures-'+v+'.json')).read_text()):
            runs.add(ROOT/record['out']);runs.add(ROOT/record['cold'])
    for r in json.loads((BASE/'save-results.json').read_text())['tests']:runs.add(ROOT/r['out'])
    raw=set();binding={}
    selected=('artifact.json','command.json','emulator.cfg','host-pacing.json','timing.json','routine-timing.json','trace-symbols.json')
    for run in runs:
        for p in run.iterdir():
            if not p.is_file():continue
            if p.suffix in ('.ram','.png','.gz') or p.name in selected or p.name in ('candidate.lbl','candidate.xex','candidate.atr') or p.name in ('pins.csv','cpu-exclusive.csv','routines.csv') and run!=BUILD/'campaign-full':
                # The full campaign's large CSV traces remain local. Samples,
                # input, native frames and all paired DLI traces are archived.
                raw.add(p)
    with zipfile.ZipFile(DOC/'capture-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(raw):
            name=str(p.relative_to(ROOT));z.write(p,name);binding[name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    dump(DOC/'capture-manifest.json',binding)
    pre=json.loads((DOC/'preflight.json').read_text());source=ROOT/'assets/levels/camp2-b/campaign.json'
    assert sha(source)==pre['campaign_sha256']
    cfg=Path.home()/'.atari800.cfg'
    assert (sha(cfg) if cfg.exists() else None)==pre['owner_config_sha256']
    old=json.loads((ROOT/'docs/recovery1/preflight.json').read_text())
    changed=[p for p,h in old['preserved_files'].items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    assert not changed,changed
    manifest=dict(base_commit=pre['HEAD_before'],branch='feature/v1-art-final-energy',
                  ATR='docs/art-final/owner-smoke/neon-shift65-v1-art-final.atr',ATR_sha256=sha(BUILD/'candidate.atr'),
                  campaign=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes_unchanged=True,levels=60,ID='131c57e2',bounds='Embedded visual_size; no source rewrite'),
                  build='python3 tools/v1_build.py --out <fresh-directory>',
                  source_dependency_inventory={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},
                  generated_input_and_NRQs={str(p.relative_to(ROOT)):sha(p) for p in sorted(generated)},
                  inventory_note='Inherited diagnostic helpers are inventory, not a claim that all were executed. cc-input are actual compiled C inputs; final generated runtime and NRQ identify the product. bands-prototype is a separate diagnostic, excluded from the delivered ATR.',
                  capture=dict(observer='build/eng3-observed-input-3pal/observer/src/atari800',observer_sha256=sha(ROOT/'build/eng3-observed-input-3pal/observer/src/atari800'),
                               base_config='docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg',base_config_sha256=sha(ROOT/'docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg'),
                               mode='SDL dummy headless only; owner launcher --check only'),
                  archives={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in (DOC/'source-inputs.zip',DOC/'capture-evidence.zip')},
                  linker_map=dict(raw_path=str((BUILD/'candidate.map').relative_to(ROOT)),raw_sha256=sha(BUILD/'candidate.map'),archived_sha256=sha(evidence/'candidate.map'),transform='Trailing whitespace/empty final lines removed; all tokens identical'),
                  preservation=dict(status='PASS',existing_files_unchanged=len(old['preserved_files']),owner_config_unchanged=True,old_ART4_RECOVERY1_artifacts_preserved=True),
                  reused_evidence=dict(path='docs/recovery1/REPORT.md',commit=pre['HEAD_before'],scope='Prior long audio, original campaign audits, untouched runtime; exact binding checked by art_final_audit'),
                  visual_owner='NOT_RUN',hardware='NOT_RUN',published=False)
    dump(DOC/'manifest.json',manifest)
    print('PASS ART-FINAL source/capture/preservation package',len(raw),'raw files',flush=True)


if __name__=='__main__':main()
