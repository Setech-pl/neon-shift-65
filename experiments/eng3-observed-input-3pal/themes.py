"""Editable pixel geometry. All coordinates are ANTIC4 logical pixels.

The robot, containers and dock contract use the frozen UX2 silhouette. Wall
devices occupy existing collision cells only; the compiler verifies this.
"""
import json,os
from pathlib import Path
AREA=int(os.environ.get('NEON_ART2_AREA','1'))
CONFIG=json.loads((Path(__file__).parent/'areas.json').read_text())
SPEC=next(a for a in CONFIG['areas'] if a['id']==AREA)

def install(c):
 if AREA==1:return
 blank,rect,line,tile=c.blank,c.rect,c.line,c.tile
 def wall(mask,kind=0):
  p=blank()
  # Equal full-size wall envelopes, distinct interior construction.
  rect(p,2,4,4,8,2)
  if mask&1:rect(p,2,0,4,6,2)
  if mask&4:rect(p,2,10,4,6,2)
  if mask&2:rect(p,4,4,4,8,2)
  if mask&8:rect(p,0,4,4,8,2)
  if AREA==2:
   # Twin transparent fluid conduits with luminous joints.
   rect(p,3,5,2,6,0)
   if mask&1:rect(p,3,0,2,6,0)
   if mask&4:rect(p,3,10,2,6,0)
   if mask&2:rect(p,4,7,4,2,0)
   if mask&8:rect(p,0,7,4,2,0)
   line(p,2,4,5,4,1);rect(p,3,7,2,2,2)
  elif AREA==3:
   # Segmented trays: interruptions are interior, boundary stays connected.
   rect(p,3,5,2,6,0)
   line(p,2,6,5,6,1);line(p,2,10,5,10,1)
   if mask&1:line(p,3,0,3,5,1)
   if mask&4:line(p,3,10,3,15,1)
   if mask&2:line(p,4,7,7,7,1)
   if mask&8:line(p,0,7,3,7,1)
   rect(p,4,8,1,1,2)
  else:
   # Shield centre and deep aperture; hazard lugs stay within the mass.
   rect(p,3,6,2,4,0);line(p,2,4,5,4,1)
   if mask&1:rect(p,3,0,2,4,1)
   if mask&4:rect(p,3,12,2,4,1)
   if mask&2:line(p,6,5,6,10,1)
   if mask&8:line(p,1,5,1,10,1)
   rect(p,2 if kind else 5,10,1,1,1)
  return tile(p)
 def floors():
  result=[]
  # Maximum six dim pixels: no vertical boundary or closed outline.
  for k in range(12):
   p=blank()
   if k:
    if AREA==2:line(p,1+(k%3),2+(k//3)*3,2+(k%3),2+(k//3)*3,3)
    elif AREA==3:line(p,k%5,1+(k//5)*5,k%5+2,1+(k//5)*5,3)
    else:line(p,1+(k%4),2+(k//4)*4,2+(k%4),2+(k//4)*4,3)
   result.append(tile(p))
  assert len(set(result))==12
  return result
 def device(kind,phase):
  w,h={'terminal':(16,32),'cabinet':(16,48),'fan':(16,32),'gate':(24,32),'installation':(32,32)}[kind]
  p=blank(w,h);rect(p,1,1,w-2,h-2,2);rect(p,2,2,w-4,h-4,0)
  line(p,1,1,w-2,1,1);line(p,1,1,1,h-2,1)
  if AREA==2:
   if kind in ('terminal','cabinet'):
    # Rounded glass reservoirs with fluid level and bubble phase.
    for top in ([5,21,35] if kind=='cabinet' else [5,20]):
     height=9 if kind=='cabinet' else 8
     line(p,5,top,10,top,2);line(p,3,top+2,3,top+height-2,2);line(p,12,top+2,12,top+height-2,2)
     line(p,5,top+height,10,top+height,2);line(p,4,top+height-3,11,top+height-3,2)
     rect(p,5+phase*2,top+3,1,1,1)
   elif kind=='fan':
    # Nutrient pump: four-position valve and side liquid pipes.
    for x in (4,11):line(p,x,5,x,26,2)
    for y in (7,23):line(p,4,y,11,y,2)
    line(p,5,15,10,15,2);rect(p,5+phase,13,1,3,1)
   elif kind=='gate':
    for x in (4,10,16):
     line(p,x,5,x,25,2);line(p,x+3,5,x+3,25,2)
    line(p,3,9,20,9,1);line(p,3,21,20,21,2)
   else:
    line(p,4,8,27,8,2);line(p,4,11,27,11,2)
    for x in (5,13,21):
     line(p,x,11,x,25,2);line(p,x,25,x+4,25,2);line(p,x+4,25,x+4,19,2)
    rect(p,5+phase*6,8,2,2,1)
  elif AREA==3:
   if kind in ('terminal','cabinet'):
    for y in range(5,h-5,7):
     rect(p,3,y,10,5,2);rect(p,4,y+1,8,3,0);line(p,5,y+2,9,y+2,2)
     rect(p,4+(phase if y==5 else 0),y+3,1,1,1)
   elif kind=='fan':
    # Optical switch: branching fibre lines and travelling port light.
    line(p,7,5,7,26,2)
    for y in (7,13,19,25):line(p,3,y,12,y,2)
    rect(p,4+phase,7,1,1,1)
   elif kind=='gate':
    for x in (4,9,14,19):line(p,x,5,x,26,2)
    for y in (6,13,20,26):line(p,3,y,20,y,1)
   else:
    for x in (4,10,16,22,28):line(p,x,6,x,25,2)
    for y in (8,16,24):line(p,4,y,28,y,2)
    rect(p,5+phase*7,15,2,2,1)
  else:
   if kind in ('terminal','cabinet'):
    for y in range(5,h-5,12):
     rect(p,3,y,10,9,2);rect(p,5,y+2,6,5,0)
     line(p,4,y+7,10,y+7,3);rect(p,4+(phase if y==5 else 0),y+3,1,1,1)
   elif kind=='fan':
    # Massive reactor valve, independent four-position spindle.
    line(p,4,7,11,7,2);line(p,4,24,11,24,2);line(p,3,9,3,22,2);line(p,12,9,12,22,2)
    line(p,5,10,10,21,3);line(p,10,10,5,21,3)
    rect(p,4+phase,9,1,1,1)
    rect(p,7,14,2,3,2)
   elif kind=='gate':
    rect(p,3,5,18,22,2);rect(p,5,7,14,18,0)
    line(p,11,7,11,24,2)
    for x in (5,9,13,17):line(p,x,25,x+2,22,3)
   else:
    for y in (6,10):line(p,3,y,28,y,3)
    for x in (5,13,21):rect(p,x,14,5,12,2);rect(p,x+1,16,3,8,0)
    rect(p,5+phase*7,7,2,2,1)
  return p
 c.wall=wall;c.floors=floors;c.device=device
 c.split=lambda p:{(x//8,y//16):tile([r[x:x+8] for r in p[y:y+16]]) for y in range(0,len(p),16) for x in range(0,len(p[0]),8)}

def loading(c):
 """Independent ANTIC C 160x64 editable line illustrations."""
 p=c.blank(160,64);line=lambda x,y,a,b:c.line(p,x,y,a,b,1)
 def box(x,y,w,h):
  line(x,y,x+w-1,y);line(x,y,x,y+h-1);line(x+w-1,y,x+w-1,y+h-1);line(x,y+h-1,x+w-1,y+h-1)
 box(14,7,132,43)
 for x in (0,159):line(x,0,14 if x==0 else 145,7);line(x,63,14 if x==0 else 145,49)
 for x in (14,45,114,145):line(x,50,max(0,min(159,80+2*(x-80))),63)
 if AREA==2:
  for x in (24,64,104):
   box(x,15,27,31);box(x+3,18,21,25);line(x+4,35,x+22,35)
   for a,b in [(x+8,26),(x+15,22),(x+18,31)]:box(a,b,2,2)
   line(x+13,9,x+13,14);line(x+13,46,x+13,52)
  line(20,10,138,10);line(20,53,138,53)
 elif AREA==3:
  for x in (22,58,94,126):
   width=25 if x!=126 else 13;box(x,13,width,35)
   for y in (17,24,31,38):box(x+3,y,width-6,5);line(x+5,y+2,x+8,y+2)
  for x in (32,69,105):line(x,9,x,12);line(x,49,x,55)
  line(18,55,141,55)
 else:
  box(55,12,50,36);box(60,17,40,26)
  line(66,22,93,22);line(66,38,93,38);line(65,23,65,37);line(94,23,94,37)
  line(68,24,91,36);line(91,24,68,36);box(77,28,6,5)
  for x in (23,117):box(x,20,19,25);box(x+4,25,11,13);line(x+9,8,x+9,19);line(x+9,46,x+9,57)
  for x in range(55,103,8):line(x,47,x+4,43)
 raw=bytes(sum(p[y][x+i]<<(7-i) for i in range(8)) for y in range(64) for x in range(0,160,8))
 return raw
