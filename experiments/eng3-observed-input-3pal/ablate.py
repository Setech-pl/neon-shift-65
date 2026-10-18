"""Single ART3 component substitution, private source/output; diagnostic only."""
import os,sys,shutil,subprocess,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
component=sys.argv[1];root=R/'build/eng1-action-semantics-and-campaign-memory/ablation'/component
S=root/'source';shutil.copytree(R/'experiments/art3-contextual-decoration',S)
p=S/'decoration.py';s=p.read_text()
if component=='border':s=s.replace('if pos in animated:return original','return original\n if pos in animated:return original')
if component=='devices':s=s.replace('if number!=0:return old','return old\n if number!=0:return old')
if component=='walls':
 s=s.replace('return int(mask in (5,10) and h(x,y,number)%11==0)','return (x//4+y//3)%2')
 s=s.replace('original=c.wall','return\n original=c.wall')
if component=='floor':
 s=s.replace('height=len(rows);width=len(rows[0]);docks=',"return {(x,y):(((y-2)*4+x-2)%12 if number==0 and y in (2,3,4) else ([0,1,0,0,4,0,0,5,0,6,0,7,0,8,0,9,0,10,11,0][x]+(2 if y%3==0 else 0))%12) for y,row in enumerate(rows) for x,c in enumerate(row) if c!='#'},[]\n height=len(rows);width=len(rows[0]);docks=")
assert component in ['border','devices','walls','floor']
p.write_text(s)
for a in [3,4]:
 out=root/f'area-{a}';env=dict(os.environ,NEON_ART2_AREA=str(a),NEON_ART2_BUILD=str(out))
 with (root/f'build-{a}.log').open('w') as f:r=subprocess.run([sys.executable,str(S/'build.py')],env=env,stdout=f,stderr=subprocess.STDOUT)
 print(component,a,r.returncode,flush=True);assert not r.returncode
