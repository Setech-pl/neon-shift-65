#!/usr/bin/env python3
"""Reuse PUBLISH1 capture/encoding with current labels, hashes and stock SIO."""
import json,hashlib,os
from pathlib import Path
import publish1_media as p
from hwvis1_prepare import binding
b=binding();p.HASHES={int(n):v['sha256'] for n,v in b['images'].items()}
p.PRODUCT=(p.ROOT/'docs/hwvis1/source-checkpoint.txt').read_text().strip()
records={}
for n,item in b['images'].items():
    data=(p.ROOT/item['build']/'candidate.lbl').read_bytes()
    records[n]=dict(text=data.decode(),sha256=hashlib.sha256(data).hexdigest())
(p.ROOT/'docs/media/capture-labels.json').write_text(json.dumps(records,indent=2)+'\n')
p.main(owner_folder='build/owner-smoke/hwvis1',work_folder='build/owner-smoke/hwvis1/media',stock=True)
