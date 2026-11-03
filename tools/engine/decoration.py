"""Offline contextual selection. No code/data structures added on Atari."""
import os
AREA=int(os.environ.get('NEON_ART2_AREA','1'))
VARIANT=os.environ.get('ART3_VARIANT','B')
def h(x,y,n=0):return ((x+17)*73856093^(y+19)*19349663^(AREA*31+n+23)*83492791)&0xffffffff

def devices(old,number,level):
 if number!=0:return old
 # Keep exactly the six original resources and each resource's period/phase.
 locations={
  1:[(2,-1),(15,2),(4,7),(-1,2),(10,-1),(8,7)],
  2:[(1,-1),(-1,2),(15,1),(11,7),(6,-1),(3,7)],
  3:[(12,7),(15,1),(-1,1),(-1,4),(1,-1),(7,-1)],
  4:[(1,7),(-1,1),(8,-1),(15,4),(11,7),(2,-1)]}[AREA]
 return [(kind,x,y,period,phase) for (kind,_,_,period,phase),(x,y) in zip(old,locations)]

def background(pos,original,animated):
 if pos in animated:return original
 r,c=divmod(pos,40);p=bytearray(8)
 if AREA==1:
  active=(r==2 and 0<=c<=8) or (r==23 and 27<=c<=38)
  if active and c%7 not in (4,5):p[4]=0x55
 elif AREA==2:
  if c==1 and 8<=r<=12 or c==38 and 14<=r<=19:p[:]=bytes([0x10]*8)
  if (r,c) in [(8,2),(18,37)]:p[4]=0x55
 elif AREA==3:
  if c==38 and r in (3,4,7,8,10):p[:]=bytes([0x04]*8)
  if r==23 and c in (6,7,8,12,13,16,17):p[2]=p[5]=0x15
 else:
  if r==2 and c in (23,24,28,29,33,34) or r==23 and c in (28,29,34,35):p[3]=0x55
  if c==1 and r in (13,14,18,19):p[2]=p[5]=0x50
 return bytes(p)

def floor_plan(rows,number,specs):
 height=len(rows);width=len(rows[0]);docks=[(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c in '.*+']
 walk=lambda x,y:0<=x<width and 0<=y<height and rows[y][x]!='#'
 eligible=[]
 for y,row in enumerate(rows):
  for x,c in enumerate(row):
   if c=='#' or any(abs(x-a)+abs(y-b)<=1 for a,b in docks):continue
   ns=[walk(x+dx,y+dy) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]]
   if sum(ns)<3:continue
   wall_distance=min(abs(x-a)+abs(y-b) for b,rr in enumerate(rows) for a,v in enumerate(rr) if v=='#')
   device_distance=min([abs(x-(a+1))+abs(y-(b+1)) for _,a,b,_,_ in specs] or [wall_distance])
   eligible.append((device_distance+wall_distance*2,h(x,y,number),x,y))
 points={(x,y) for _,_,x,y in eligible}
 adjacent=lambda x,y:[(a,b) for a,b in points if abs(a-x)+abs(b-y)==1]
 anchors=[]
 for _,_,x,y in sorted(eligible):
  if not adjacent(x,y):continue
  if all(abs(x-a)+abs(y-b)>=4 for a,b in anchors):anchors.append((x,y))
  if len(anchors)>={1:3,2:4,3:3,4:2}[AREA]:break
 choices={1:[4,5,6,10],2:[1,4,7,10],3:[2,5,8,11],4:[1,5,9]}
 clustered=set(anchors)
 for x,y in anchors:
  near=sorted(adjacent(x,y),key=lambda p:h(*p,number+51))
  clustered.update(near[:1])
 result={}
 for _,_,x,y in eligible:
  distance=min([abs(x-a)+abs(y-b) for a,b in anchors] or [99])
  if (x,y) in clustered or distance==1 and (h(x,y,number)>>8)%4 < (2 if AREA==2 else 0):
   result[x,y]=choices[AREA][(h(x,y,number+11)>>12)%len(choices[AREA])]
 return result,anchors

def wall_kind(mask,x,y,number):
 return int(mask in (5,10) and h(x,y,number)%11==0)

def install(c):
 original=c.wall
 def wall(mask,kind=0):
  data=original(mask,0 if VARIANT=='B' and mask in (5,10) else kind)
  if VARIANT!='B' or not kind or mask not in (5,10):return data
  p=c.decode_tile(data)
  # Two low-luminance service notches, strictly interior. All boundary pixels
  # remain bit-identical, including required and absent connected arms.
  if AREA in (1,4):p[6][3]=3;p[9][4]=0
  elif AREA==2:p[7][3]=3;p[8][4]=2
  else:p[6][3]=1;p[10][4]=3
  return c.tile(p)
 c.wall=wall
