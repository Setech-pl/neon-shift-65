"""Seal ART3 finalB, prior trials and read-only preservation evidence."""
from pathlib import Path
import hashlib,json,subprocess,gzip,tarfile,shutil
B=Path('build/eng3-observed-input-3pal');D=Path('docs/checkpoints/art3-contextual-decoration');E=D/'evidence';R=Path('build/eng3-observed-input-3pal-review');FINAL=R/'candidate-v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
pre=json.loads((B/'preflight.json').read_text());bad=[p for p,h in pre['guards'].items() if not Path(p).exists() or sha(p)!=h];assert not bad,bad
home=Path.home()/'.atari800.cfg';assert (sha(home) if home.exists() else None)==pre['home_config']
bind=json.loads((B/'candidate-binding.json').read_text());assert all(sha(p)==h for group in ['sources','variants'] for p,h in bind[group].items())
for a,h in bind['ATR'].items():
 assert sha(D/f'area-{a}/candidate.atr')==h
 launch=json.loads((B/f'area-{a}/owner-smoke/launch.json').read_text());assert launch['display_mode']=='windowed' and '-windowed' in launch['command'] and '-no-autosave-config' in launch['command'] and launch['sha256']==h
 shutil.copy2(B/f'area-{a}/owner-smoke/launch.json',D/f'area-{a}/owner-launch-check.json')
for p in B.glob('*.json'):shutil.copy2(p,E/p.name)
for p in R.glob('*.json'):shutil.copy2(p,E/('reviewer-'+p.name))
for p in FINAL.glob('*.json'):
 (E/'reviewer').mkdir(exist_ok=True);shutil.copy2(p,E/'reviewer'/p.name)
write(E/'preservation.json',dict(status='PASS',protected_files=len(pre['guards']),old_file_mismatches=bad,home_config_unchanged=True,source_binding='PASS',ATR_binding='PASS',agent_GUI='NOT_RUN',Void_Strike='No tools invoked against project',merge=False,push=False))
selected=set()
for p in B.glob('*.json'):selected.add(p)
for a in range(1,5):
 root=B/f'area-{a}'
 for p in root.rglob('*.json'):selected.add(p)
 for case in ['game-accepted-replay','game-accepted-hud','open/game-accepted-replay','game-accepted-repeat','game-accepted-small-ui','game-accepted-attract']:
  p=root/case
  for q in p.glob('*'):
   if q.is_file() and (q.suffix in ['.lbl','.cfg'] or q.name in ['timeline.csv','publication.csv','input-clock.csv','frame-schedule.csv','cpu-exclusive.csv']):selected.add(q)
  caps=json.loads((p/'artifact.json').read_text())['captures'];frames={caps[0],caps[-1],950}&set(caps)
  if case=='game-accepted-replay':
   checks=json.loads((p/'fixture-result.json').read_text())['checks'];frames.update([checks[68]['frame']+3,checks[-1]['frame']+3])
  for f in frames:
   for stem,ext in [('native','png'),('frame','ram'),('raster','ram')]:
    q=p/f'{stem}-{f:04}.{ext}'
    if q.exists():selected.add(q)
 for case in ['game-accepted-dock','atlas-static/capture','atlas-inverse/capture','atlas-states/capture','atlas-connections/capture','loader-fast','loader-slow']:
  for p in (root/case).glob('*'):
   if p.is_file() and p.suffix in ['.ram','.png','.lbl','.cfg']:selected.add(p)
 selected.add(root/'native-film/audio-validation.json')
for slot in ['candidate-v1','baseline-focused','trial-area3-A']:
 root=R/slot
 for p in root.glob('*.json'):selected.add(p)
 for case in root.iterdir():
  if not case.is_dir() or case.name=='clean-rebuild-final':continue
  focused=case.name.startswith(('undo311-','RZ200-','RS311-'))
  for p in case.rglob('*'):
   if not p.is_file():continue
   if p.suffix in ['.json','.png','.ram','.lbl','.cfg'] or focused and p.suffix in ['.atr','.csv','.log'] or p.name in ['cpu-exclusive.csv','input-clock.csv','frame-schedule.csv','register-writes.csv']:selected.add(p)
for p in R.glob('*'):
 if p.is_file() and p.suffix in ['.json','.log']:selected.add(p)
for p in FINAL.glob('*.log'):selected.add(p)
for root in [Path('experiments/eng3-observed-input-3pal'),Path('experiments/eng3-observed-input-3pal-review')]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in str(p):selected.add(p)
for p in (B/'trial-area3-A').rglob('*'):
 if p.is_file() and (p.suffix in ['.json','.nrq'] or p.name in ['candidate.atr','carry.atr']):selected.add(p)
for a in range(1,5):selected.add(Path(f'build/art2-four-area-themes/area-{a}/phase-accepted/ART2-comparison.json'))
selected.add(Path('docs/checkpoints/art2-neon-palettes/phase-classification.json'))
manifest={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(selected)}
archive=E/'selected-evidence.tar.gz'
with archive.open('wb') as dest,gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w|') as tf:
 for p in sorted(selected):
  info=tf.gettarinfo(str(p),arcname=str(p));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with p.open('rb') as src:tf.addfile(info,src)
with tarfile.open(archive,'r:gz') as tf:
 members=tf.getmembers();assert len(members)==len(manifest)
 for m in members:
  f=tf.extractfile(m);h=hashlib.sha256()
  while b:=f.read(1024*1024):h.update(b)
  assert h.hexdigest()==manifest[m.name]['sha256'],m.name
write(E/'portable-evidence-manifest.json',dict(archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,verified=True,members=manifest))
print('Portable verified',len(manifest),archive.stat().st_size,flush=True)
raw={}
for root in [*(B/f'area-{a}' for a in range(1,5)),R,B/'trial-area3-A']:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in str(p):raw[str(p)]=dict(sha256=sha(p),bytes=p.stat().st_size)
write(E/'raw-evidence-manifest.json',dict(scope='Local raw author/reviewer final, baseline and trial evidence; selected portable subset separately verified.',files=raw))
cp=dict(iteration='ART3 contextual decoration',branch='feature/art3-contextual-decoration',base=pre['base'],HEAD_before_checkpoint_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),HEAD_role='The local checkpoint commit contains this snapshot; resolve git log -1 feature/art3-contextual-decoration. Self-referential commit hash intentionally excluded.',revision=bind['revision'],statuses=dict(ART_DECORATION='PASS four areas, normal replay and resources',QUALIFICATION='FAIL: new ART3 area3 boundary regression',ENGINE='FAIL: area3 new NO_UNDO_IMAGE/RZ->ZR, area4 inherited failures; historical failures remain',REPLAY='PASS69/11/4 full69undo collisions',REBUILD='PASS author128/128 independent64/64',INDEPENDENT_REVIEW='PASS art scope; rejects overall qualification',M1_OWNER='PENDING',LISTENING='NOT_RUN',HARDWARE='NOT_RUN',SIO2SD='NOT_RUN'),areas=[dict(id=a,ATR=dict(path=str(D/f'area-{a}/candidate.atr'),sha256=bind['ATR'][str(a)],bytes=1048592)) for a in range(1,5)],resources=dict(MAIN_free=80,MAIN_extreme_free=32,LOW_free=75,banks=5,RAW=8624,encoded=8768,active_reserved_union=46610,peak_reserved_union=46994,resident_growth=0,buffers_growth=0,min_free_glyphs=[55,51,55,51]),source_freeze=dict(path=str(E/'candidate-binding.json'),sha256=sha(E/'candidate-binding.json')),review=dict(path=str(D/'review.md'),sha256=sha(D/'review.md')),portable=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)),preserved_files=len(pre['guards']),owner_launcher='python3 experiments/eng3-observed-input-3pal/owner_smoke.py --area N',display='Explicit WINDOWED',merge=False,push=False,production_integration=False)
write(D/'checkpoint.json',cp)
write(D/'manifest.json',dict(files={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='manifest.json'}))
print('PASS preservation',len(pre['guards']),'raw',len(raw),'qualification FAIL explicit',flush=True)
