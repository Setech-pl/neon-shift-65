"""ENG3-B-v1 oracle: device returns -> requests -> independent XSB history.

No accepted-action list, candidate gs or rendered RAM is an input here.
Short pair/triple fixtures do not reach the initial 14-heartbeat repeat.
Repeat fixtures separately exercise Detector with supplied capture heartbeats.
"""
import csv, json, hashlib
from pathlib import Path

VERSION = 'ENG3-B-v1-oracle-1'
PAL = 35568
ADDRS = (0xd300, 0xd010, 0xd01f)
DIR = {1:'U', 2:'D', 4:'L', 8:'R'}
MASK = {0xd300:15, 0xd010:1, 0xd01f:7}

def runtime_read_pcs(xex):
    """Locate literal LDA device queries in immutable linked code, not state."""
    import sys
    sys.path.insert(0, 'tools')
    from atr import chunks
    result = {}
    records, _ = chunks(Path(xex).read_bytes())
    for start, data in records:
        for i in range(len(data)-2):
            if data[i] == 0xad:
                addr = int.from_bytes(data[i+1:i+3], 'little')
                if addr in ADDRS: result[start+i] = addr
    return result

def transactions(bus, pcs=None):
    """Fixed protocol, never choose boundaries from candidate actions."""
    current=[];result=[];filtered=0
    for q in bus:
        if pcs is not None and int(q['pc']) not in pcs:
            filtered+=1;continue
        address=int(q['address'])
        if not current and address!=ADDRS[0]:
            if pcs is not None: raise AssertionError(('unexpected query',q))
            filtered+=1;continue
        if address!=ADDRS[len(current)]:
            if pcs is not None: raise AssertionError(('incomplete observation',current,q))
            current=[];filtered+=1;continue
        current.append(q)
        if len(current)==3:
            result.append(dict(number=len(result)+1,completed=int(q['clock']),
                frame=int(q['frame']),values=[int(r['value'])&MASK[a] for r,a in zip(current,ADDRS)],
                queries=[dict(clock=int(r['clock']),address=int(r['address']),
                    value=int(r['value'])&MASK[a],pc=int(r.get('pc',0))) for r,a in zip(current,ADDRS)]))
            current=[]
    # Window can begin/end inside a probe. The caller reports that limitation.
    return result,dict(filtered_non_runtime_queries=filtered,trailing_queries=len(current),
        grouping='literal runtime LDA PCs + PORTA/TRIG0/CONSOL' if pcs else 'legacy address grouping; corroborated separately against CPU')

class Detector:
    def __init__(self):
        self.buttons=0;self.direction=None;self.frames=0;self.armed=False
    def consume(self,values,heartbeat=False):
        stick,trigger,console=values
        buttons=(not trigger)|((not(console&2))<<1)|((not(console&4))<<2)|((not(console&1))<<3)
        edges=buttons&~self.buttons;self.buttons=buttons
        if edges&4:return ['OPTION']
        direction=next((c for bit,c in DIR.items() if not(stick&bit)),None)
        move=None
        if direction!=self.direction:
            self.direction=direction;self.frames=14;self.armed=heartbeat;move=direction
        elif direction and heartbeat:
            if not self.armed:self.armed=True
            else:
                if self.frames:self.frames-=1
                if not self.frames:self.frames=5;move=direction
        result=[move] if move else []
        if edges&3:result.append('Z')
        if edges&8:result.append('S')
        return result

class Game:
    def __init__(self,rows,seed=0):
        self.rows=rows;self.player=next([x,y] for y,row in enumerate(rows) for x,c in enumerate(row) if c in '@+')
        self.boxes=[[x,y] for y,row in enumerate(rows) for x,c in enumerate(row) if c in '$*']
        self.moves=self.pushes=seed;self.history=[];self.paused=False
    def state(self):
        return dict(player=self.player[:],boxes=[p[:] for p in self.boxes],moves=self.moves,pushes=self.pushes)
    def wall(self,p):
        x,y=p;return y<0 or y>=len(self.rows) or x<0 or x>=len(self.rows[y]) or self.rows[y][x]=='#'
    def request(self,c):
        accepted=False
        if c=='S':self.paused=True;accepted=True
        elif c=='Z':
            if self.history:
                s=self.history.pop();self.player=s['player'];self.boxes=s['boxes'];self.moves=s['moves'];self.pushes=s['pushes'];accepted=True
        elif c in 'UDLR':
            dx,dy={'U':(0,-1),'D':(0,1),'L':(-1,0),'R':(1,0)}[c]
            p=[self.player[0]+dx,self.player[1]+dy];pushed=p in self.boxes
            target=[p[0]+dx,p[1]+dy]
            if not self.wall(p) and (not pushed or (not self.wall(target) and target not in self.boxes)):
                self.history.append(self.state());self.history=self.history[-256:]
                if pushed:self.boxes[self.boxes.index(p)]=target;self.pushes=(self.pushes+1)&0xffffffff
                self.player=p;self.moves=(self.moves+1)&0xffffffff;accepted=True
        return dict(action=c,accepted=int(accepted),undo=len(self.history),state=self.state())

def origin(action,observation,waveform):
    index=0 if action in 'UDLR' else 1 if action=='Z' else 2
    query=observation['queries'][index]['clock'];t0=None;old=(15,1,7)
    for event in waveform:
        clock,*values=event
        if clock>=query:break # device read precedes equal-clock edge
        if action in 'UDLR':active=values[0]!=15;changed=values[0]!=old[0]
        elif action=='Z':active=values[1]==0 or not(values[2]&2);changed=values[1]!=old[1] or (values[2]&2)!=(old[2]&2)
        else:active=not(values[2]&1);changed=(values[2]&1)!=(old[2]&1)
        if active and changed:t0=clock
        old=values
    if t0 is None:raise AssertionError(('no external origin',action,observation))
    return t0

def expected(observations,rows,waveform,prefix='',seed=0):
    game=Game(rows,seed);detector=Detector();requests=[]
    for c in prefix:game.request(c)
    tfirst=min(e[0] for e in waveform)
    # Window opens neutral and after fixture prelude, before tfirst.
    for o in observations:
        events=detector.consume(o['values'])
        if o['completed']<tfirst:continue
        for c in events:
            if c=='OPTION':raise AssertionError('OPTION outside pair/triple oracle scope')
            request=game.request(c)
            requests.append(dict(**request,observation=o['number'],completed=o['completed'],t0=origin(c,o,waveform)))
            if c=='S':return requests
    return requests

def self_check():
    d=Detector();assert d.consume([7,0,6])==['R','Z','S']
    assert d.consume([7,0,6])==[]
    assert d.consume([15,1,7])==[]
    assert d.consume([7,0,7])==['R','Z']
    d=Detector();assert d.consume([7,1,7],True)==['R']
    for _ in range(13):assert d.consume([7,1,7],True)==[]
    assert d.consume([7,1,7],True)==['R']
    for _ in range(4):assert d.consume([7,1,7],True)==[]
    assert d.consume([7,1,7],True)==['R']
    g=Game(['#####','#@$.#','#####']);a=g.request('R');b=g.request('Z')
    assert a['accepted'] and b['accepted'] and b['state']['moves']==0
    assert not g.request('Z')['accepted'] and not g.request('U')['accepted']

def board_matches(ram,expected,rows,sections):
    """Expected screen codes from immutable package and independent game state."""
    desc=sections[0x9de0];bx,by=desc[2:4];composition=sections[0x1400]
    for y,row in enumerate(rows):
        for x,ground in enumerate(row):
            if ground=='#':continue
            player=[x,y]==expected['player'];box=[x,y] in expected['boxes'];dock=ground in '.*+'
            bases=[124] if player else [4,12,16,20] if box and dock else [0] if box else [8] if dock else [None]
            valid=False
            for base in bases:
                codes=[]
                for q in range(4):
                    rr=by+2*y+q//2;band=0 if rr<2 else 4 if rr>=18 else (rr-2)//4
                    want=124+q if player else desc[8+band*24+base+q] if base is not None else composition[y*80+x*4+q]
                    codes.append(ram[0x8800+rr*40+bx+2*x+q%2]==want)
                if all(codes):valid=True;break
            if not valid:return False
    return True

if __name__=='__main__':
    self_check();print(VERSION,'independent tie/history/release/repeat checks PASS')
