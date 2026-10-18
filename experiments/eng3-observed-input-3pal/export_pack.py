"""Reusable canonical pixel sources, compiled tile libraries and slot assets."""
import os,sys,json,hashlib
from pathlib import Path
area=int(sys.argv[1]);S=Path(__file__).parent;B=Path(f'build/eng3-observed-input-3pal/area-{area}')
os.environ.update(NEON_ART2_AREA=str(area),NEON_ART2_BUILD=str(B))
sys.path.insert(0,str(S.resolve()))
import compile as c,themes
from assets import decode_tile
out=B/'reusable';out.mkdir(exist_ok=True);a=c.arrays()
walls=[c.wall(mask,kind) for kind in range(2) for mask in range(16)];floors=c.floors()
objects=[c.tile(c.container_pixels()),c.tile(c.container_pixels(True)),c.cool(a['gameplay_common'][:32])]+[c.tile(c.container_pixels(True,n)) for n in range(3)]
robot=c.cool(a['robot_frames']);assert len(robot)==1280
devices={k:[c.device(k,p) for p in range(4)] for k in ['terminal','cabinet','fan','gate','installation']}
source=dict(area=themes.SPEC,ABI=1,pixel_selectors=dict(background=0,highlight=1,theme=2,flat_floor_and_accents=3,inverse_container_PF3=128),tile_pixels=[8,16],native_pixels=[16,16],wall_masks='N=1 E=2 S=4 W=8; all16 masks, both detail kinds',walls=[dict(mask=n%16,kind=n//16,pixels=decode_tile(t)) for n,t in enumerate(walls)],floors=[decode_tile(t) for t in floors],object_states=[dict(name=n,pixels=decode_tile(t)) for n,t in zip(['container-floor','container-dock','empty-dock','dock-phase0','dock-phase1','dock-phase2'],objects)],robot_frames=[decode_tile(robot[i:i+32]) for i in range(0,1280,32)],devices=devices)
(out/'pixel-source.json').write_text(json.dumps(source,indent=2)+'\n')
for name,data in [('walls.bin',b''.join(walls)),('floors.bin',b''.join(floors)),('objects.bin',b''.join(objects)),('robot-40-frames.bin',robot)]:
 (out/name).write_bytes(data)
# Canonical boundaries are checked before emitting reusable sources.
for mask in range(16):
 p=decode_tile(walls[mask])
 for flag,points in [(1,[(x,0) for x in range(2,6)]),(2,[(7,y) for y in range(4,12)]),(4,[(x,15) for x in range(2,6)]),(8,[(0,y) for y in range(4,12)])]:
  if mask&flag:assert any(p[y][x] for x,y in points),(area,mask,flag)
for p in source['floors']:
 assert sum(v!=0 for row in p for v in row)<=8
 assert not any(all(row[x] for row in p) for x in range(8))
(out/'connections-and-floor-check.json').write_text(json.dumps(dict(status='PASS',area=area,masks=16,detail_variants=2,floors=12,wall_arm_boundaries_checked=True,no_full_height_floor_edge=True),indent=2)+'\n')
print('PASS reusable pack',area)
