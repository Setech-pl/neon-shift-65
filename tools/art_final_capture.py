#!/usr/bin/env python3
"""Real paired ATR captures, legal inputs, save/resume and unchanged geometry."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from product1_gauntlet import setup
from product1_fix1_review import live,sections
from camp2_solver import replay
import gauntlet
import verify

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('build/art-final')
STICK={'U':14,'D':13,'L':11,'R':7}
BUILDS={'before':Path('build/recovery1/owner-vis1r2'),
        'final':BASE/'final','bands':BASE/'bands-prototype'}
SEMANTIC=('scene','phase','player','boxes','moves','pushes','undo')


def capture(variant):
    build=BUILDS[variant];labs=setup(build);native=gauntlet.run
    levels=json.loads(Path('assets/levels/camp2-b/campaign.json').read_text())['levels']
    image=(build/'candidate.atr').read_bytes();results=[]
    routines=['_display_counters','_game_step','_undo_pop','_display_changed','_display_animate','publish_update','_music_update','_art_final_bands']
    def probe(name,disk,events,frames,total):
        def run(*args,**kw):kw['atr']=str(disk);kw['routines']=routines;return native(*args,**kw)
        gauntlet.run=run
        try:out=gauntlet.probe(name,events,sorted(set(frames)),total,boot=True)
        finally:gauntlet.run=native
        return out,{f:verify.state(out/f'frame-{f:04}.ram',labs) for f in sorted(set(frames))}
    for number in (1,5,9):
        events=[(700,700,dict(fire=0))];f=1000
        def move(path):
            nonlocal f
            for ch in path:events.append((f,f,dict(stick=STICK[ch])));f+=8
        for level in levels[:number-1]:
            move(level['path']);events.append((f+20,f+20,dict(fire=0)));f+=320
        level=levels[number-1];path=level['path'];frames=[]
        initial=f-5;frames+=list(range(initial,initial+5));f+=32
        move(path);won=f+12;settled=f+80;frames += [won,settled];f+=96
        undo=[]
        for _ in path:events.append((f,f,dict(consol=5)));undo.append(f+5);f+=8
        restored=f+12;frames+=undo+[restored];f+=32
        prefix=path[:max(1,len(path)//2)];move(prefix);partial=f+12;frames.append(partial);f+=32
        events.append((f,f,dict(consol=6)));frames.append(f+20);f+=40
        events.append((f,f,dict(consol=5)));f+=320;menu=f-5;frames.append(menu)
        out,states=probe('art-final-'+variant+f'-{number:02d}',build/'candidate.atr',events,frames,f+20)
        start=states[initial];assert start['scene']==number-1 and start['phase']==1 and start['moves']==start['undo']==0
        for frame in [initial,won,settled,restored,partial]+undo:
            s=states[frame];assert s['error']==s['overflow']==s['publication_overflow']==0
            live(out,frame,labs,sections(image,number-1))
        assert states[won]['phase']==states[settled]['phase']==2
        for i,frame in enumerate(undo):
            expected=path[:len(path)-i-1];p,b,ps=replay(level['rows'],expected);s=states[frame]
            assert s['moves']==len(expected) and s['pushes']==len(ps) and s['player']==list(p) and sorted(s['boxes'])==sorted(map(list,b))
        assert all(states[restored][k]==start[k] for k in SEMANTIC)
        g=labs['_gs'];assert (out/f'frame-{initial:04}.ram').read_bytes()[g:g+793]==(out/f'frame-{restored:04}.ram').read_bytes()[g:g+793]
        assert states[menu]['phase']==0
        cold,ss=probe('art-final-'+variant+f'-{number:02d}-cold',out/'candidate.atr',
                     [(700,700,dict(stick=13)),(720,720,dict(fire=0)),(1250,1250,dict(consol=5)),(1280,1280,dict(consol=3))],
                     [1200,1260,1595],1620)
        for frame in (1200,1260):
            assert all(ss[frame][k]==states[partial][k] for k in ('scene','player','boxes','moves','pushes'))
            assert ss[frame]['undo']==0;live(cold,frame,labs,sections(image,number-1))
        assert all(ss[1595][k]==start[k] for k in SEMANTIC)
        live(cold,1595,labs,sections(image,number-1))
        record=dict(variant=variant,number=number,size=level['visual_size'],out=str(out),cold=str(cold),
                    initial=initial,won=won,settled=settled,restored=restored,partial=partial,
                    states={str(frame):states[frame] for frame in (initial,won,settled,restored,partial)},
                    undo_frames=undo,config_sha256=hashlib.sha256((out/'emulator.cfg').read_bytes()).hexdigest(),
                    input_sha256=hashlib.sha256(gzip.decompress((out/'input.gz').read_bytes())).hexdigest(),status='PASS')
        results.append(record)
        (BASE/('captures-'+variant+'.json')).write_text(json.dumps(results,indent=2)+'\n')
        print('PASS ART-FINAL capture',variant,number,'solve/all undo/cold save/restart/native raster',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('variant',choices=BUILDS);a=p.parse_args();capture(a.variant)


if __name__=='__main__':main()
