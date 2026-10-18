#!/usr/bin/env python3
"""Author original puzzles by reversible pulls; independently solve and dedup D4."""
import hashlib,json,random,sys
from collections import deque
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from solver import parse,solve_path,DIRS
ROOT=Path(__file__).resolve().parents[1]

def canonical(rows):
    # Strip ALL surrounding walls: filled external padding and translations
    # never make a puzzle unique. Retain each interior wall/target/object.
    cells={(x,y):c for y,r in enumerate(rows) for x,c in enumerate(r) if c!='#'}
    variants=[]
    for mirror in (1,-1):
        for turn in range(4):
            v={}
            for (x,y),c in cells.items():
                x*=mirror
                for _ in range(turn):x,y=-y,x
                v[x,y]=c
            ox=min(x for x,y in v);oy=min(y for x,y in v)
            variants.append(tuple(sorted((x-ox,y-oy,c) for (x,y),c in v.items())))
    return hashlib.sha256(repr(min(variants)).encode()).hexdigest()

def authored(rng,boxes_n):
    w=rng.randint(7,11);h=rng.randint(5,7)
    floor={(x,y) for y in range(1,h-1) for x in range(1,w-1)}
    for cell in rng.sample(sorted(floor),rng.randint(1,max(1,len(floor)//5))):floor.remove(cell)
    if len(floor)<boxes_n*4:return
    seen={min(floor)};q=list(seen)
    for x,y in q:
        for dx,dy in DIRS.values():
            p=x+dx,y+dy
            if p in floor and p not in seen:seen.add(p);q.append(p)
    if seen!=floor:return
    targets=set(rng.sample(sorted(floor),boxes_n));boxes=targets.copy();player=rng.choice(sorted(floor-boxes))
    pulls=0
    # Reverse Sokoban: player walks, optionally pulls a crate from behind.
    for _ in range(rng.randint(180,500)):
        dx,dy=rng.choice(list(DIRS.values()));np=player[0]+dx,player[1]+dy
        if np not in floor or np in boxes:continue
        behind=player[0]-dx,player[1]-dy
        if behind in boxes and rng.random()<0.8:
            boxes.remove(behind);boxes.add(player);pulls+=1
        player=np
    if boxes==targets or pulls<boxes_n*2 or any(b in targets for b in boxes):return
    # Embed in the established 16x8 art footprint, no change to renderer.
    rows=[['#']*16 for _ in range(8)]
    for x,y in floor:rows[y][x]='.' if (x,y) in targets else ' '
    for x,y in boxes:rows[y][x]='*' if (x,y) in targets else '$'
    x,y=player;rows[y][x]='+' if player in targets else '@'
    rows=[''.join(r) for r in rows]
    try:path,states=solve_path('\n'.join(rows),max_states=100000)
    except ValueError:return
    if path is None or len(path)<5+boxes_n*2 or len(path)>180:return
    walls,_,bb,p,_,_=parse('\n'.join(rows));pushes=0;changes=0;prev=None
    for c in path:
        dx,dy=DIRS[c];np=p[0]+dx,p[1]+dy
        if np in bb:
            bb.remove(np);bb.add((np[0]+dx,np[1]+dy));pushes+=1
        if prev and prev!=c:changes+=1
        prev=c;p=np
    if pushes<boxes_n*2:return
    return dict(rows=rows,path=path,solver_states=states,moves=len(path),pushes=pushes,turns=changes,canonical=canonical(rows),score=pushes*3+changes+len(path)//3)

def main():
    dest=ROOT/'assets/levels/product1-campaign.json'
    if dest.exists():raise SystemExit('Refusing to replace authored campaign')
    rng=random.Random(65042026);chosen=[];keys=set()
    for n,count in [(1,5),(2,15),(3,25),(4,15)]:
        pool=[];tries=0
        while len(pool)<count*2:
            tries+=1;l=authored(rng,n)
            if l and l['canonical'] not in keys:
                keys.add(l['canonical']);pool.append(l)
                print(n,len(pool),'tries',tries,'score',l['score'],flush=True)
        pool.sort(key=lambda l:l['score'])
        chosen.extend(pool[(i*(len(pool)-1))//(count-1)] for i in range(count))
    for l in chosen:l['difficulty_rank']=l['score']+10*sum(c in '$*' for r in l['rows'] for c in r)
    chosen.sort(key=lambda l:l['difficulty_rank'])
    areas=['ENERGY','HYDROPONIC','DATA HUB','REACTOR']
    for i,l in enumerate(chosen):l.update(number=i+1,area=i//15+1,name=f'{areas[i//15]} {i%15+1:02d}/15')
    dest.write_text(json.dumps(dict(version=1,authoring='Original deterministic reverse-pull generator tools/product1_campaign.py; no imported level collection',seed=65042026,uniqueness='D4 plus translation, all non-wall cells and objects',difficulty='Increasing crate count, then solver push/turn/step score within each tier; owner play review pending',levels=chosen),indent=2)+'\n')
    print('PASS',dest,len(chosen),flush=True)
if __name__=='__main__':main()
