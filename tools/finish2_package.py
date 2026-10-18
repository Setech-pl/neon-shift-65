#!/usr/bin/env python3
"""Seal the five clean FINISH2 ATRs, actual source inputs and raw evidence."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/finish2';BASE=ROOT/'build/finish2';BUILD=BASE/'final'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main():
    verification=json.loads((DOC/'verification.json').read_text());assert verification['status']=='PASS'
    evidence=DOC/'evidence';evidence.mkdir(exist_ok=True)
    for src,name in ((BUILD/'build.log','build.log'),(BUILD/'campaign-full/campaign-result.json','campaign-result.json'),
                     (BUILD/'campaign-full/timing.json','timing.json'),(BUILD/'native-campaign/result.json','native-result.json'),
                     (BUILD/'native-campaign/replay.log','native-replay.log'),(BUILD/'eng4/eng4-result.json','eng4-result.json')):
        shutil.copyfile(src,evidence/name)
    delivered=[]
    for name,folder,n in [('neon-shift65-v1.0-RC2','final',None)]+[(f'neon-shift65-v1.0-RC2-test-{n:02}',f'test-{n}',n) for n in (1,16,31,46)]:
        src=BASE/folder/'candidate.atr';dest=DOC/'owner-smoke'/(name+'.atr')
        assert src.read_bytes()==dest.read_bytes()
        header=(BASE/folder/'campaign-id.h').read_text()
        identity=hashlib.sha256(b'FINISH2 hardware test '+str(n).encode()+(ROOT/'assets/levels/camp2-b/campaign.json').read_bytes()).digest()[:4] if n else bytes.fromhex('131c57e2')
        if n:assert 'save_id[4]={'+','.join(map(str,identity))+'}' in header
        launch=BASE/'owner-smoke'/name/'launch.json';record=json.loads(launch.read_text());assert record['supplied_atr_sha256']==sha(src)
        shutil.copyfile(launch,evidence/(name+'-launch.json'))
        delivered.append(dict(name=name+'.atr',path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size,
                              test_start=n,save_identity=identity.hex(),build=str((BASE/folder).relative_to(ROOT)),
                              main_free=verification['memory'][folder]['MAIN_free']))
    assert len({d['save_identity'] for d in delivered})==5
    (DOC/'SHA256-ATR.txt').write_text(''.join(d['sha256']+'  owner-smoke/'+d['name']+'\n' for d in delivered))
    lines=['# FINISH2 — pięć czystych ATR-ów','',
           'Każdy obraz: 1 048 592 B. Wszystkie zawierają tę samą pełną kampanię 60 poziomów. Sumy dotyczą czystych dysków przed pierwszym zapisem.',
           '', '| ATR | Start na czystym dysku | SHA-256 |','|---|---|---|']
    for d in delivered:
        lines.append(f"| [{d['name']}](owner-smoke/{d['name']}) | "+(str(d['test_start']) if d['test_start'] else 'zwykłe menu')+f" | `{d['sha256']}` |")
    lines += ['', '[Wszystkie ATR-y + instrukcja ZIP](neon-shift65-v1.0-RC2-hardware.zip), [SHA256-ATR.txt](SHA256-ATR.txt), [test sprzętowy](START-HERE.md), [raport](REPORT.md).']
    (DOC/'ARTIFACTS.md').write_text('\n'.join(lines)+'\n')
    with zipfile.ZipFile(DOC/'neon-shift65-v1.0-RC2-hardware.zip','w',zipfile.ZIP_DEFLATED) as z:
        for d in delivered:z.write(ROOT/d['path'],d['name'])
        for name in ('START-HERE.md','SHA256-ATR.txt'):
            # Keep checksum paths valid after extracting the hardware bundle.
            if name=='SHA256-ATR.txt':z.writestr(name,(DOC/name).read_text().replace('owner-smoke/',''))
            else:
                text=(DOC/name).read_text().replace('[Pięć ATR-ów i ich SHA-256](ARTIFACTS.md)',
                    'Pięć ATR-ów i ich SHA-256: patrz SHA256-ATR.txt w tym katalogu')
                text=text.replace('[raporcie](REPORT.md)','raporcie FINISH2 w repo (docs/finish2/REPORT.md)')
                z.writestr(name,text)
    prior=json.loads((ROOT/'docs/finish1/manifest.json').read_text())
    sources={ROOT/p for p in prior['source_dependency_inventory']}
    sources.update((ROOT/'tools').glob('finish2_*.py'));sources.add(ROOT/'experiments/finish2/art.py')
    sources.add(ROOT/'tools/product1_eng4.py')
    generated=set()
    for folder in ('final','test-1','test-16','test-31','test-46','rebuild-final'):
        b=BASE/folder
        generated.update(p for p in (b/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.o'))
        generated.update((b/'cc-input').glob('*.c'))
        generated.update(p for p in b.iterdir() if p.is_file() and p.suffix in ('.c','.h','.s','.inc','.cfg','.map','.lbl'))
    generated.update(BUILD.glob('art-area-*/level-*/scene-0.nrq'))
    generated.update(BUILD.glob('art-area-*/level-*/scene-0-banks.json'))
    with zipfile.ZipFile(DOC/'source-inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(sources|generated):z.write(p,str(p.relative_to(ROOT)))
    runs={BUILD/'campaign-full',BUILD/'eng4',BUILD/'presentation-patch',BUILD/'presentation-stock',
          ROOT/'build/finish1/rc1/finish2-before-patch',ROOT/'build/finish1/rc1/finish2-before-stock'}
    runs.update(Path(r['out']) for r in json.loads((DOC/'runtime.json').read_text())['tests'])
    raw=set()
    selected={'artifact.json','command.json','emulator.cfg','host-pacing.json','timing.json','routine-timing.json','trace-symbols.json',
              'timeline.csv','sio.csv','cpu-exclusive.csv','frame-schedule.csv','input-clock.csv','eng4-result.json','fetch-oracle.json',
              'pins.csv','fixed-pin-events.csv','device-reads.csv','action-state.csv','control-writes.csv','antic-reads.csv'}
    for run in runs:
        for p in run.iterdir():
            if p.is_file() and (p.suffix in ('.ram','.png','.gz') or p.name in selected):raw.add(p.resolve())
    captures={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(raw)}
    dump(DOC/'capture-manifest.json',captures)
    with zipfile.ZipFile(DOC/'capture-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(raw):z.write(p,str(p.relative_to(ROOT)))
    dump(DOC/'manifest.json',dict(candidate='NEON SHIFT 65 v1.0-RC2 / FINISH2',base_commit=verification['base'],
         artifacts=delivered,campaign_path='assets/levels/camp2-b/campaign.json',campaign_sha256=verification['campaign_sha256'],
         campaign_bytes_preserved=True,all60_campaign_sectors_identical_across_five_ATRs=True,
         source_dependency_inventory={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},
         actual_generated_inputs={str(p.relative_to(ROOT)):sha(p) for p in sorted(generated)},
         archives={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in DOC.glob('*.zip')},
         observer=dict(path='build/eng3-observed-input-3pal/observer/src/atari800',sha256=sha(ROOT/'build/eng3-observed-input-3pal/observer/src/atari800'),
                       mode='headless SDL dummy; owner launcher --check only',config='docs/checkpoints/vis1-energy-industrial-restore/capture-base.cfg'),
         clean_rebuild_identical=True,verification_sha256=sha(DOC/'verification.json'),runtime_sha256=sha(DOC/'runtime.json'),
         hardware='NOT_RUN',visual_owner='PENDING',published=False,pushed=False))
    (DOC/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DOC)}\n' for p in sorted(DOC.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
    print('PASS sealed five ATRs, source inputs,',len(raw),'raw evidence files',flush=True)

if __name__=='__main__':main()
