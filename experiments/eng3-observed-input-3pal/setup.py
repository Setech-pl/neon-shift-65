"""Create isolated ENG2 inputs; never rewrite ENG1 or shared runtime."""
from pathlib import Path
import hashlib,json,subprocess,shutil
R=Path(__file__).resolve().parents[2]
S=Path(__file__).parent; B=R/'build/eng3-observed-input-3pal'
D=R/'docs/checkpoints/eng3-observed-input-3pal'; E=D/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
old=R/'docs/checkpoints/eng1-action-semantics-and-campaign-memory'
binding=json.loads((old/'evidence/candidate-binding-v5.json').read_text())
checks=[]
for p,h in binding['sources'].items():
 q=R/p;checks.append(dict(path=p,expected=h,actual=sha(q),kind='source'))
for p,h in binding['variants'].items():
 q=R/p;checks.append(dict(path=p,expected=h,actual=sha(q),kind='ATR'))
assert all(x['expected']==x['actual'] for x in checks)
cp=json.loads((old/'checkpoint.json').read_text())
for a in cp['areas']:
 p=R/a['ATR']['path'];assert sha(p)==a['ATR']['sha256']
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z']).decode().split('\0')
write(E/'preflight.json',dict(base=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),branch=subprocess.check_output(['git','branch','--show-current']).decode().strip(),ENG1_checks=checks,ENG1_final=cp['areas'],untracked_preserved=[p for p in untracked if p and 'eng3-observed-input-3pal' not in p],AGENTS='none in repo or ancestor directories',restrictions='headless/--check only; no shared config, Void Strike, merge/push/integration'))
base=R/'experiments/eng1-action-semantics-and-campaign-memory-v5'
for p in base.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 target=S/p.relative_to(base)
 assert not target.exists(),target
 target.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix=='.py':target.write_text(p.read_text().replace('eng1-action-semantics-and-campaign-memory-v5','eng3-observed-input-3pal'))
 else:shutil.copyfile(p,target)
write(E/'runtime-equivalence.json',{str(p.relative_to(base)):dict(ENG1=sha(p),ENG2=sha(S/p.relative_to(base))) for p in base.rglob('*') if p.is_file() and p.suffix in ('.c','.h','.s','.cfg','.xsb','.solution','.json')})
B.mkdir(parents=True,exist_ok=True)
print('ENG1 closure verified; ENG2 isolated input prepared',len(checks))
