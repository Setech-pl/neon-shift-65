#!/usr/bin/env python3
"""Build a deterministic player ZIP from the unchanged normal distribution ATR."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from publish1_prepare import ROOT,PRODUCT,HASHES,sha

def main():
    dist=ROOT/'dist';atr=dist/'neon-shift65-v1.0.0.atr';assert sha(atr.read_bytes())==HASHES[0]
    files={atr.name:atr.read_bytes()}
    for name in ('LICENSE','LICENSE-ASSETS','THIRD_PARTY_NOTICES.md'):
        files[name]=(ROOT/name).read_bytes()
    for p in sorted((ROOT/'docs/licenses').iterdir()):files['docs/licenses/'+p.name]=p.read_bytes()
    for name in ('how-to-play.md','how-to-play.pl.md','quick-start.md','quick-start.pl.md'):
        text=(ROOT/'docs'/name).read_text().replace('[dist](../dist/)','[package contents](../README.md)')
        files['docs/'+name]=text.encode()
    for name in ('README.md','README.pl.md'):
        src='release-notes.md' if name=='README.md' else 'release-notes.pl.md'
        text=(ROOT/'docs'/src).read_text().replace('release-notes.pl.md','README.pl.md').replace('release-notes.md','README.md')
        files[name]=text.encode()
    archive=dist/'neon-shift65-v1.0.0.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            i=zipfile.ZipInfo(name,date_time=(2026,10,18,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data)
    with zipfile.ZipFile(archive) as z:
        assert z.read(atr.name)==atr.read_bytes()
        assert sum(n.endswith('.atr') for n in z.namelist())==1
        assert set(z.namelist())==set(files)
        assert not any(b'/Users/' in data or b'/private/tmp/' in data for data in files.values())
    def version(tool):
        r=subprocess.run([tool,'--version'],capture_output=True,text=True);return (r.stdout+r.stderr).strip().splitlines()[0]
    manifest={'version':'1.0.0','status':'DRAFT','product_source_commit':PRODUCT,
      'packaging_commit':'Resolve git log -1 -- dist/manifest.json; deliberately not self-referential.',
      'campaign_source':'assets/levels/camp2-b/campaign.json','campaign_sha256':sha((ROOT/'assets/levels/camp2-b/campaign.json').read_bytes()),
      'normal_atr':{'file':atr.name,'sha256':HASHES[0],'bytes':atr.stat().st_size,'player_save':'empty sectors 8100 and 8101'},
      'player_zip':{'file':archive.name,'sha256':sha(archive.read_bytes()),'entries':list(sorted(files))},
      'tools':{'packaging_python':sys.version.split()[0],'cl65':version('cl65'),'ca65':version('ca65'),'ld65':version('ld65'),'sim65':version('sim65'),'node':version('node'),'clang':version('clang'),'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]},
      'provenance':'ATR recovered byte-for-byte from product checkpoint, not rebuilt for relocation. Source inputs locked in docs/publish1/source-inputs.json. Historical production package cc65 2.19 reports binary V2.18.',
      'tests':'Unchanged product: RELEASE1 campaign60/finale/undo256/save/coldContinue/OS SIO; independent A-01/A-02/A-03 CLOSED. No new full engine audit.',
      'acceptance':{'hardware':'OWNER_PENDING','appearance':'OWNER_PENDING','rights':'OPEN: see THIRD_PARTY_NOTICES.md'},
      'owner_smoke':'python3 tools/publish1_prepare.py --routes; generated and ignored build/owner-smoke/',
      'archive_entries_sha256':{n:sha(data) for n,data in sorted(files.items())}}
    (dist/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (dist/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in (atr,archive,dist/'manifest.json')))
    print('PASS deterministic ZIP, same normal ATR, no saves/ROM/config/local paths; SHA256SUMS written')
if __name__=='__main__':main()
