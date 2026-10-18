#!/usr/bin/env python3
"""PUBLISH2: reuse deterministic PUBLISH1 package layout for HWVIS1 candidate."""
import json
from pathlib import Path
import publish1_package as p
from hwvis1_prepare import binding
b=binding();p.PRODUCT=(p.ROOT/'docs/hwvis1/source-checkpoint.txt').read_text().strip();p.HASHES={int(n):v['sha256'] for n,v in b['images'].items()}
p.main()
f=p.ROOT/'dist/manifest.json';m=json.loads(f.read_text())
m.update(status='OWNER_PENDING',provenance='HWVIS1 clean locked-source builds; two isolated snapshots reproduced the normal ATR byte-for-byte. docs/hwvis1/source-inputs.json and REPORT.md.',tests='60 solutions + finale from finished ATR under standard OS SIO; undo256/restart/save/cold Continue; A-01 witness and phase sweep; A-02/A-03 regression. Emulator evidence only.',owner_smoke='python3 tools/hwvis1_prepare.py; build/owner-smoke/hwvis1/; hold OPTION on Atari power-on (BASIC OFF)')
f.write_text(json.dumps(m,indent=2)+'\n')
(p.ROOT/'dist/SHA256SUMS').write_text(''.join(f'{p.sha(q.read_bytes())}  {q.name}\n' for q in [p.ROOT/'dist/neon-shift65-v1.0.0.atr',p.ROOT/'dist/neon-shift65-v1.0.0.zip',f]))
