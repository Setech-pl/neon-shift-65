"""Evidence-only host pacing wrapper; target clocks and frozen ATR unchanged.

Intercept only the emulator process, save its actual argv/config before launch.
The frozen playback/probes and PAL clock definition are unchanged.
"""
import json,runpy,subprocess,sys
from pathlib import Path
original_run=subprocess.run
def run(argv,*args,**kwargs):
    if isinstance(argv,list) and argv and str(argv[0]).endswith('/atari800'):
        argv=list(argv);argv.append('-turbo')
        cfg=Path(argv[argv.index('-config')+1]);text=cfg.read_text().replace('TURBO_SPEED=1','TURBO_SPEED=0');cfg.write_text(text)
        (cfg.parent/'command.json').write_text(json.dumps(argv,indent=2)+'\n')
        (cfg.parent/'host-pacing.json').write_text(json.dumps(dict(mode='-turbo, TURBO_SPEED=0',target='same PAL35568 clocks/frame; no target code or input modifications'),indent=2)+'\n')
        kwargs['timeout']=1800
    return original_run(argv,*args,**kwargs)
subprocess.run=run
if __name__=='__main__':
    script=sys.argv[1];sys.argv=sys.argv[1:];sys.path.insert(0,str(Path(script).parent.resolve()));runpy.run_path(script,run_name='__main__')
