"""Verify delivered final package, bindings and explicit qualification failure."""
from pathlib import Path
import hashlib,json,tarfile
D=Path('docs/checkpoints/art3-contextual-decoration')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
cp=json.loads((D/'checkpoint.json').read_text());manifest=json.loads((D/'manifest.json').read_text())['files'];bad=[p for p,v in manifest.items() if not Path(p).exists() or sha(p)!=v['sha256'] or Path(p).stat().st_size!=v['bytes']];assert not bad,bad
assert cp['statuses']['QUALIFICATION'].startswith('FAIL') and cp['statuses']['ENGINE'].startswith('FAIL')
binding=json.loads(Path(cp['source_freeze']['path']).read_text())
for group in ['sources','variants']:
 for p,h in binding[group].items():assert sha(p)==h,p
for a in cp['areas']:assert sha(a['ATR']['path'])==a['ATR']['sha256']
p=json.loads((D/'evidence/portable-evidence-manifest.json').read_text());assert sha(p['archive'])==p['sha256'];count=0
with tarfile.open(p['archive'],'r:gz') as tf:
 for m in tf:
  h=hashlib.sha256();f=tf.extractfile(m)
  while b:=f.read(1024*1024):h.update(b)
  assert h.hexdigest()==p['members'][m.name]['sha256'];count+=1
assert count==len(p['members'])
print('PASS delivered manifest',len(manifest),'portable members',count,'runtime freeze and4 ATR; qualification/ENGINE FAIL retained')
