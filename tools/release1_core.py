#!/usr/bin/env python3
"""Audit media and current campaign in Python, ASan/UBSan and sim65.
Adapted from independent-audit-claude/repro/audit_core.py; original preserved.
"""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path

ROOT=Path.cwd(); B=Path(sys.argv[1]); O=B/'independent-core';O.mkdir(exist_ok=True)
levels=json.loads((ROOT/'assets/levels/camp2-b/campaign.json').read_text())['levels']
def crc(data):
    c=65535
    for b in data:
        c^=b<<8
        for _ in range(8):c=((c<<1)^0x1021 if c&0x8000 else c<<1)&65535
    return c
def sector(d,n):return d[16+(n-1)*128:16+n*128]
def initial(l):
    r=l['rows'];p=next((x,y) for y,row in enumerate(r) for x,c in enumerate(row) if c in '@+')
    boxes=[(x,y) for y,row in enumerate(r) for x,c in enumerate(row) if c in '$*']
    return p,boxes,0,0
def step(l,s,ch,required=False):
    p,boxes,m,push=s; boxes=list(boxes); dx,dy={'U':(0,-1),'D':(0,1),'L':(-1,0),'R':(1,0)}[ch]
    q=p[0]+dx,p[1]+dy
    legal=0<=q[0]<16 and 0<=q[1]<8 and l['rows'][q[1]][q[0]]!='#'
    if legal and q in boxes:
        b=q[0]+dx,q[1]+dy
        legal=0<=b[0]<16 and 0<=b[1]<8 and l['rows'][b[1]][b[0]]!='#' and b not in boxes
        if legal:boxes[boxes.index(q)]=b;push+=1
    if required:assert legal,(l['number'],m,ch)
    return (q,boxes,m+1,push) if legal else s
def hash_sig(s):
    p,boxes,m,push=s
    data=bytes(p)+bytes(v for b in boxes for v in b)+struct.pack('<II',m,push)
    h=0x9e37
    for b in data:h=((h*33)^b)&65535
    return h

image=(B/'candidate.atr').read_bytes();identity=hashlib.sha256((ROOT/'assets/levels/camp2-b/campaign.json').read_bytes()).digest()[:4]
assert len(image)==16+8192*128 and image[:2]==b'\x96\x02' and int.from_bytes(image[4:6],'little')==128
catalog=sector(image,1000);assert catalog[:6]==b'NSCD\x01\x3c' and catalog[8:12]==identity and crc(catalog[:126])==int.from_bytes(catalog[126:],'little')
stats=[];paths=[];sigs=[]
for i,l in enumerate(levels):
    assert l['number']==i+1 and l['area']==i//15+1 and len(l['rows'])==8 and all(len(r)==16 for r in l['rows'])
    row=l['rows'];p,boxes,_,_=initial(l);targets={(x,y) for y,r in enumerate(row) for x,c in enumerate(r) if c in '.*+'}
    assert len(boxes)==len(targets) and 1<=len(boxes)<=10
    sec=sector(image,1100+i*70)
    assert sec[:12]==b'NSLV'+bytes([1,i,l['area'],len(boxes),*p,16,8]) and sec[12:16]==identity
    assert crc(sec[:126])==int.from_bytes(sec[126:],'little')
    for y in range(8):
        for x in range(16):
            c=row[y][x];n=y*16+x;t=(sec[16+n//4]>>(2*(n%4)))&3
            assert t==(0 if c=='#' else 2 if c in '.*+' else 1)
    assert sec[48:48+2*len(boxes)]==bytes(v for b in boxes for v in b)
    assert sec[68:68+len(l['name'])]==l['name'].encode()
    payload=b''.join(sector(image,1101+i*70+j) for j in range(69))[:8768]
    expected=(B/f"art-area-{l['area']}/level-{i+1:02}/scene-0.nrq").read_bytes();assert payload==expected
    assert payload[:6]==b'NSRQ\x02\x01' and payload[6]==9 and crc(payload[:14])==int.from_bytes(payload[14:16],'little')
    assert crc(payload[16:144])==int.from_bytes(payload[12:14],'little') and crc(payload[144:])==int.from_bytes(payload[10:12],'little')
    for j,(addr,size) in enumerate(zip((0x8c00,0xa000,0xa400,0xa800,0xac00,0x9800,0x1400,0xb160,0x9de0),(1024,)*5+(880,800,1280,544))):
        a,n,off,c=struct.unpack_from('<4H',payload,16+8*j);assert (a,n)==(addr,size) and crc(payload[144+off:144+off+n])==c
    s=initial(l);states=[s];sig=[]
    for ch in l['path']:s=step(l,s,ch,True);states.append(s);sig.append(hash_sig(s))
    assert set(s[1])==targets
    paths.append(l['path']);sigs.append(sig)
    stats.append(dict(level=i+1,moves=s[2],pushes=s[3],final_player=s[0],final_boxes=s[1],initial_player=p,boxes=len(boxes),goals=len(targets)))

c='#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n#include "game.h"\n#include "undo.h"\n'
for i,l in enumerate(levels):
    c+=f'static const char *r{i}[]={{'+','.join(json.dumps(r) for r in l['rows'])+'};\n'
    c+=f'static const unsigned int e{i}[]={{'+','.join(map(str,sigs[i]))+'};\n'
trial_sigs=[[hash_sig(step(l,initial(l),d)) for d in 'UDLR'] for l in levels]
trial_moves=[[step(l,initial(l),d)[2] for d in 'UDLR'] for l in levels]
c+='static const unsigned int trials[60][4]={' + ','.join('{'+','.join(map(str,a))+'}' for a in trial_sigs)+'};\n'
c+='static const unsigned char trial_moves[60][4]={' + ','.join('{'+','.join(map(str,a))+'}' for a in trial_moves)+'};\n'
c+='static const Level levels[]={'+','.join('{r'+str(i)+',8,"audit"}' for i in range(60))+'};\n'
c+='static const char *paths[]={'+','.join(map(json.dumps,paths))+'};\n'
c+='static const unsigned int *expected[]={'+','.join('e'+str(i) for i in range(60))+'};\n'
c+='''static struct {unsigned char pre[16];GameState g;unsigned char post[16];} guard;
static GameState prefix;
static unsigned int hash(void){unsigned int h=0x9e37;unsigned char i;unsigned char *p;
h=(h*33)^guard.g.player.x;h=(h*33)^guard.g.player.y;
for(i=0;i<guard.g.box_count;i++){h=(h*33)^guard.g.boxes[i].x;h=(h*33)^guard.g.boxes[i].y;}
p=(unsigned char *)&guard.g.moves;for(i=0;i<8;i++)h=(h*33)^p[i];return h&65535U;}
static void check_guard(void){unsigned char i;for(i=0;i<16;i++){assert(guard.pre[i]==0xa5);assert(guard.post[i]==0x5a);}}
int main(void){unsigned char i,p,d;unsigned int j,n,cut,keep;signed char dx,dy;
memset(guard.pre,0xa5,16);memset(guard.post,0x5a,16);assert(undo_configure(256));
for(i=0;i<60;i++){
for(d=0;d<4;d++){assert(game_start(&guard.g,&levels[i]));dx=dy=0;if(d==0)dy=-1;if(d==1)dy=1;if(d==2)dx=-1;if(d==3)dx=1;
assert(game_step(&guard.g,dx,dy,&p)==trial_moves[i][d]);assert(hash()==trials[i][d]);check_guard();}
assert(game_start(&guard.g,&levels[i]));n=strlen(paths[i]);keep=n>256?256:n;cut=n-keep;if(!cut)prefix=guard.g;
for(j=0;j<n;j++){dx=dy=0;switch(paths[i][j]){case 'U':dy=-1;break;case 'D':dy=1;break;case 'L':dx=-1;break;case 'R':dx=1;break;}
assert(game_step(&guard.g,dx,dy,&p));assert(hash()==expected[i][j]);check_guard();if(j+1==cut)prefix=guard.g;}
assert(level_is_solved(&guard.g));assert(undo_count()==keep);
for(j=0;j<keep;j++){assert(undo_pop(&guard.g));if(n-j-1)assert(hash()==expected[i][n-j-2]);check_guard();}
assert(!undo_pop(&guard.g));assert(!memcmp(&guard.g,&prefix,sizeof(prefix)));}
puts("All campaign steps, 60 wins, retained undo prefixes, guards OK");return 0;}
'''
(O/'oracle.c').write_text(c)
def run(args):
    with (O/'run.log').open('a') as f:subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,check=True)
run(['clang','-std=c99','-fsanitize=address,undefined','-g','-Isrc',O/'oracle.c','src/level.c','src/game.c','src/undo.c','-o',O/'host']);run([O/'host'])
objs=[]
for i,f in enumerate([O/'oracle.c',B/'level.c',Path('src/game.c'),B/'undo.c']):
    o=O/f'{i}.o';run(['cl65','-t','sim6502','-DNATIVE_MOVE','-Oirs','-Cl','-Isrc','-c','-o',o,f]);objs.append(o)
for name in ('move','undo-fast'):
    o=O/(name+'.o');run(['ca65','-t','sim6502','-DNATIVE_SIM65','-o',o,B/f'source/{name}.s']);objs.append(o)
run(['cl65','-t','sim6502','-o',O/'target',*objs]);run(['sim65',O/'target'])
(O/'result.json').write_text(json.dumps(dict(levels=stats,total_steps=sum(map(len,paths)),status='PASS',identity=identity.hex(),media='all 60 board sectors and all 60 exact graphics packages'),indent=2)+'\n')
print('PASS independent media, Python oracle, C sanitizer and real 6502 movement/undo')
