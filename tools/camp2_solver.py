#!/usr/bin/env python3
"""Push-state BFS with explicit resource status. No campaign writes.

Reachable player components are merged. First solution minimizes pushes,
but walking between pushes is only shortest locally, not globally.
"""
from collections import deque
from time import monotonic
from solver import parse, DIRS


def solve_reference(rows, seconds=30, max_states=500000):
    walls, goals, boxes, player, w, h = parse('\n'.join(rows))
    floor = {(x,y) for y in range(h) for x in range(w)} - walls
    # Static reverse push reachability: stronger than corner pruning, sound.
    live = set(goals)
    todo = list(goals)
    for x,y in todo:
        for dx,dy in DIRS.values():
            prev, support = (x-dx,y-dy),(x-2*dx,y-2*dy)
            if prev in floor and support in floor and prev not in live:
                live.add(prev); todo.append(prev)

    def walk(p,b):
        paths={p:''};q=[p]
        for x,y in q:
            for d,(dx,dy) in DIRS.items():
                nxt=x+dx,y+dy
                if nxt in floor and nxt not in b and nxt not in paths:
                    paths[nxt]=paths[x,y]+d;q.append(nxt)
        return paths

    boxes=frozenset(boxes);reach=walk(player,boxes)
    start=(boxes,min(reach));parents={start:None}
    queue=deque([(start,player)]);deadline=monotonic()+seconds
    while queue:
        if monotonic()>deadline:
            return dict(status='UNKNOWN',reason='time limit',states=len(parents))
        key,p=queue.popleft();b,_=key
        if b==goals:
            segments=[]
            while parents[key] is not None:
                key,segment=parents[key];segments.append(segment)
            path=''.join(reversed(segments))
            return dict(status='SOLVED',path=path,states=len(parents),moves=len(path),
                        pushes=len(segments),metric='minimum pushes; moves NOT globally optimal')
        reach=walk(p,b)
        for box in sorted(b):
            x,y=box
            for d,(dx,dy) in DIRS.items():
                dest,support=(x+dx,y+dy),(x-dx,y-dy)
                if dest not in live or dest in b or support not in reach:continue
                nb=(b-{box})|{dest};nr=walk(box,nb);nk=(nb,min(nr))
                if nk in parents:continue
                if len(parents)>=max_states:
                    return dict(status='UNKNOWN',reason='state limit',states=len(parents))
                parents[nk]=(key,reach[support]+d);queue.append((nk,box))
    return dict(status='UNSOLVABLE',reason='exhaustive sound-pruned push graph',states=len(parents))


def solve(rows, seconds=30, max_states=500000):
    """Same exhaustive graph as solve_reference, using bitset flood fills."""
    walls,goals,boxes,p,w,h=parse('\n'.join(rows))
    stride=w+2
    bit=lambda q:1 << (q[1]*stride+q[0])
    floor=sum(bit((x,y)) for y,r in enumerate(rows) for x,c in enumerate(r) if c!='#')
    goal=sum(map(bit,goals));start_boxes=sum(map(bit,boxes))
    dirs=[('U',-stride),('D',stride),('L',-1),('R',1)]
    shift=lambda b,d:b<<d if d>=0 else b>>-d
    def flood(player,occupied):
        allowed=floor^occupied;reach=player
        while True:
            nxt=(reach | reach<<1 | reach>>1 | reach<<stride | reach>>stride)&allowed
            if nxt==reach:return reach
            reach=nxt
    live=goal
    while True:
        nxt=live
        for _,d in dirs:nxt|=shift(live,-d)&floor&shift(floor,d)
        if nxt==live:break
        live=nxt
    if start_boxes&~live:return dict(status='UNSOLVABLE',reason='static reverse-push dead square',states=0)
    reach=flood(bit(p),start_boxes);start=(start_boxes,reach&-reach)
    parents={start:None};q=deque([start]);deadline=monotonic()+seconds
    while q:
        if monotonic()>deadline:return dict(status='UNKNOWN',reason='time limit',states=len(parents))
        key=q.popleft();occupied,anchor=key
        if occupied==goal:
            plan=[]
            while parents[key] is not None:
                key,box,char=parents[key];plan.append((box,char))
            plan.reverse();player=p;bb=set(boxes);path=''
            for b,d in plan:
                index=b.bit_length()-1;box=(index%stride,index//stride);dx,dy=DIRS[d]
                support=box[0]-dx,box[1]-dy
                paths={player:''};todo=[player]
                for x,y in todo:
                    if support in paths:break
                    for ch,(ax,ay) in DIRS.items():
                        n=x+ax,y+ay
                        if 0<=n[0]<w and 0<=n[1]<h and n not in walls and n not in bb and n not in paths:
                            paths[n]=paths[x,y]+ch;todo.append(n)
                path+=paths[support]+d;bb.remove(box);bb.add((box[0]+dx,box[1]+dy));player=box
            return dict(status='SOLVED',path=path,states=len(parents),moves=len(path),pushes=len(plan),
                        metric='minimum pushes; moves NOT globally optimal')
        reach=flood(anchor,occupied);b=occupied
        while b:
            box=b&-b;b-=box
            for char,d in dirs:
                dest=shift(box,d)
                if not(dest&live) or dest&occupied or not(shift(box,-d)&reach):continue
                nb=occupied^box^dest;nr=flood(box,nb);nk=nb,nr&-nr
                if nk in parents:continue
                if len(parents)>=max_states:return dict(status='UNKNOWN',reason='state limit',states=len(parents))
                parents[nk]=(key,box,char);q.append(nk)
    return dict(status='UNSOLVABLE',reason='exhaustive sound-pruned push graph',states=len(parents))


def replay(rows,path):
    walls,goals,boxes,p,w,h=parse('\n'.join(rows));pushes=[]
    for i,d in enumerate(path):
        dx,dy=DIRS[d];n=p[0]+dx,p[1]+dy
        assert n not in walls
        if n in boxes:
            dest=n[0]+dx,n[1]+dy
            assert dest not in boxes and dest not in walls
            boxes.remove(n);boxes.add(dest)
            pushes.append(dict(step=i+1,direction=d,source=n,dest=dest,off_goal=n in goals,to_goal=dest in goals))
        p=n
    return p,boxes,pushes


def state_rows(rows,path):
    p,b,_=replay(rows,path)
    return [''.join(('*' if c in '.*+' else '$') if (x,y) in b else
                    ('+' if c in '.*+' else '@') if (x,y)==p else
                    '.' if c in '.*+' else '#' if c=='#' else ' '
                    for x,c in enumerate(row)) for y,row in enumerate(rows)]
