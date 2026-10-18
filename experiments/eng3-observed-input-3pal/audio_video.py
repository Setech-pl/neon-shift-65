"""Complete real-time headless native frames/POKEY PCM from each final ATR."""
import os,sys,json,subprocess,wave,csv,hashlib
from pathlib import Path
area=int(sys.argv[1]);B=Path(f'build/eng3-observed-input-3pal/area-{area}')
os.environ['NEON_A5C_BUILD']=str(B)
sys.path.insert(0,str(Path('experiments/renderer-a5c').resolve()))
import gauntlet,turbo_run
from emulator_smoke import run as native
original=turbo_run.original_run
def paced(argv,*a,**kw):
 if isinstance(argv,list) and argv and str(argv[0]).endswith('/atari800'):
  argv=[s for s in argv if s not in ['-turbo','-nortime']]
  cfg=Path(argv[argv.index('-config')+1]);cfg.write_text(cfg.read_text().replace('TURBO_SPEED=1','TURBO_SPEED=0'))
  (cfg.parent/'command.json').write_text(json.dumps(argv,indent=2)+'\n');kw['timeout']=180
 return original(argv,*a,**kw)
subprocess.run=paced
os.environ['NEON_A5B_OBSERVER']=str(Path('build/ux1-menu-splash-loader-crates-review/observer-v2/src/atari800').resolve())
os.environ['UX1_AUDIO_START_FRAME']='1'
out=B/'native-film';out.mkdir(exist_ok=True)
os.environ['UX1_REGISTER_LOG']=str((out/'register-writes.csv').resolve());os.environ['UX1_REGISTER_RANGE']='1,1300'
path=json.loads((B/'solutions.json').read_text())[0]['path'][:14]
events=[(700,700,dict(fire=0))]+[(1000+i*12,1000+i*12,dict(stick={'R':7,'L':11,'U':14,'D':13}[c])) for i,c in enumerate(path)]+[(1180,1180,dict(fire=0)),(1192,1192,dict(stick={'R':7,'L':11,'U':14,'D':13}[path[-1]]))]
def run(n,*a,**kw):kw['boot']=True;return native(str(out.relative_to('build')),*a,**kw)
gauntlet.ROOT=B;gauntlet.run=run;gauntlet.probe('native-film',events,list(range(1,1301)),1300,boot=True,audio=True)
with wave.open(str(out/'native-audio.wav'),'rb') as w:
 duration=w.getnframes()/w.getframerate();samples=w.getnframes();rate=w.getframerate()
expected=1299*35568/1773447;assert abs(duration-expected)<.03,(duration,expected)
r=[{k:int(v) for k,v in row.items()} for row in csv.DictReader((out/'register-writes.csv').open())]
starts=[v for v in r if v['address']==0xd400 and v['value']==34 and v['vcount']==0 and v['dlist_before']==0x8800]
cells=[v for v in r if starts[0]['frame']<=v['frame']<=starts[-1]['frame'] and (v['address']&0xffef)==0xd201 and v['value']>=160]
assert len(starts)==250 and len(cells)==3000
(out/'audio-validation.json').write_text(json.dumps(dict(status='PASS',area=area,ATR_SHA256=hashlib.sha256((B/'candidate.atr').read_bytes()).hexdigest(),real_time_headless=True,frames=1300,PCM_seconds=duration,expected_seconds=expected,samples=samples,sample_rate=rate,splash_frames=250,cassette_cells=3000,events=events),indent=2)+'\n')
print('PASS complete native film+PCM',area,duration,flush=True)
