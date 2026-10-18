#!/usr/bin/env python3
"""Replay all newly integrated maps with C sanitizers and real 6502 movement.

Witnesses may exceed undo256. Retain exactly their last256 moves and compare
the full state to the independently saved forward prefix at that boundary.
"""
import argparse
import json
import subprocess
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--build',default='build/art-final/final');a=p.parse_args()
    build=Path(a.build);out=build/'native-campaign';out.mkdir(exist_ok=False)
    levels=json.loads(Path('assets/levels/camp2-b/campaign.json').read_text())['levels']
    c='#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n#include "game.h"\n#include "undo.h"\n'
    for i,level in enumerate(levels):c+=f'static const char *r{i}[]={{'+','.join(json.dumps(r) for r in level['rows'])+'};\n'
    c+='static const Level levels[]={'+','.join('{r'+str(i)+',8,"V1"}' for i in range(60))+'};\n'
    c+='static const char *paths[]={'+','.join(json.dumps(level['path']) for level in levels)+'};\n'
    c+='''static GameState g,expected;
int main(void){unsigned char i,p;unsigned int j,n,keep,cut;signed char dx,dy;const char *s;
undo_configure(256);
for(i=0;i<60;i++){
    assert(game_start(&g,&levels[i]));s=paths[i];n=strlen(s);keep=n>256?256:n;cut=n-keep;
    if(!cut)expected=g;
    for(j=0;j<n;j++){
        dx=dy=0;switch(s[j]){case 'U':dy=-1;break;case 'D':dy=1;break;case 'L':dx=-1;break;case 'R':dx=1;break;default:assert(0);}
        assert(game_step(&g,dx,dy,&p));if(j+1==cut)expected=g;
    }
    assert(level_is_solved(&g));assert(g.moves==n);assert(undo_count()==keep);
    for(j=0;j<keep;j++)assert(undo_pop(&g));assert(!undo_pop(&g));assert(!undo_count());
    assert(!memcmp(&g,&expected,sizeof(g)));
}
puts("PASS60 new witnesses; exact last256 undo; full retained-prefix state");return 0;}
'''
    (out/'replay.c').write_text(c)
    def run(argv,log):subprocess.run(list(map(str,argv)),stdout=log,stderr=subprocess.STDOUT,check=True)
    with (out/'replay.log').open('w') as log:
        run(['clang','-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-g','-Isrc',out/'replay.c','src/level.c','src/game.c','src/undo.c','-o',out/'replay-host'],log)
        run([out/'replay-host'],log)
        objects=[]
        for i,f in enumerate((out/'replay.c',build/'level.c',Path('src/game.c'),build/'undo.c')):
            obj=out/f'sim-{i}.o';run(['cl65','-t','sim6502','-DNATIVE_MOVE','-Oirs','-Cl','-Isrc','-c','-o',obj,f],log);objects.append(obj)
        for name in ('move','undo-fast'):
            obj=out/(name+'.o');run(['ca65','-t','sim6502','-DNATIVE_SIM65','-o',obj,build/f'source/{name}.s'],log);objects.append(obj)
        run(['cl65','-t','sim6502','-o',out/'replay-target',*objects],log);run(['sim65',out/'replay-target'],log)
    result=dict(status='PASS',levels=60,longest_witness=max(len(l['path']) for l in levels),
                witnesses_exceeding_256=[l['number'] for l in levels if len(l['path'])>256],
                host='C ASan/UBSan',target='6502 move.s and undo-fast.s in sim65',
                undo='Capacity256 unchanged; exact state after undo(min(path,256)) equals forward prefix; empty undo is inert')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
