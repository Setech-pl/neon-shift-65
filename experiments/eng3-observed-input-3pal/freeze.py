"""Freeze runtime sources and all64 ATRs before independent final review."""
from pathlib import Path
import hashlib,json
B=Path('build/eng3-observed-input-3pal');S=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[p for p in S.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix in ['.s','.c','.h','.cfg','.json','.xsb','.solution','.mjs','.txt']]
paths += [S/n for n in ['compile.py','build.py','themes.py','early.py','loading_art.py','splash_assets.py','artwork.py','decoration.py']]
paths += [p for root in ['src','assets','cfg','tools'] for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
f=dict(revision='art3-final',base='b1eb77f1c713f9a2fdbc67e084e40b9120a123b4',sources={str(p):sha(p) for p in sorted(set(paths))},ATR={str(a):sha(B/f'area-{a}/candidate.atr') for a in range(1,5)},variants={str(p):sha(p) for a in range(1,5) for fixture in ['', 'open'] for p in (B/f'area-{a}'/fixture).glob('*.atr')},oracle=str(S/'palette-oracle.json'))
(B/'candidate-binding.json').write_text(json.dumps(f,indent=2)+'\n');print(json.dumps(f['ATR'],indent=2))
