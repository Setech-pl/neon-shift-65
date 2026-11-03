#!/usr/bin/env python3
"""Export the committed public source tree, excluding Git and build outputs."""
import argparse, subprocess
p=argparse.ArgumentParser(); p.add_argument('--out', required=True); a=p.parse_args()
subprocess.run(['git','archive','--format=zip','--prefix=neon-shift65-source/','-o',a.out,'HEAD'],check=True)
