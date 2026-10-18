#!/usr/bin/env python3
"""Run PUBLISH1 RGB/package/link checks against current HWVIS1 inputs."""
import publish1_verify as p
from hwvis1_prepare import binding
b=binding();p.HASHES={int(n):v['sha256'] for n,v in b['images'].items()};p.PRODUCT=(p.ROOT/'docs/hwvis1/source-checkpoint.txt').read_text().strip()
p.main(workdir='build/owner-smoke/hwvis1/media',reportdir='docs/hwvis1',freshbuild='build/hwvis1/clean-a/build/normal/candidate.atr',current=True)
