#!/usr/bin/env python3
"""Read-only emulator probes of real cold ATR boots; optional stock OS SIO."""
import argparse
from pathlib import Path
from product1_gauntlet import setup
import gauntlet

STAGES=['_main','_hardware_init','_startup','_title','_load_package',
        '_board_load','_prepare','_show_play','_show_menu','_activate',
        '_loading_begin','_loading_finish','_save_scan','_save_write','_show_ui']

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True)
    p.add_argument('--name',required=True);p.add_argument('--stock',action='store_true')
    a=p.parse_args();b=Path(a.build);setup(b)
    fire=3200 if a.stock else 700
    captures=[400,650,fire+15,fire+50,fire+100,fire+295,fire+500]
    gauntlet.probe(a.name,[(fire,fire,dict(fire=0))],captures,fire+520,
                   patch=not a.stock,boot=True,trace_override=STAGES)

if __name__=='__main__':main()
