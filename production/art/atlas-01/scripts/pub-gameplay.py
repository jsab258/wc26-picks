"""Draw chosen perception and meeting opportunities; not a simulation result."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
from draw import *
s=80;ox=65;oy=385
def t(p):return ox+p[0]*s,oy+p[1]*s
def box(z,col):u,v,w,h=z;return rect(ox+u*s,oy+v*s,w*s,h*s,col,INK,1)
b=box([0,0,6,8],'#dbd0bb')+box([0,-2,6,2],'#d4cbb8')
for z in M['ground_zones']:
    if z['id'] in ['stair','counter','backbar','snug','store']:b+=box(z['box'],z['colour'])
for f in M['furniture']:b+=box(f['box'],'#927258')
for a,c in [('street_witness','#923f51'),('partial_view_target','#b67e25'),('blocked_target','#923f51'),('overhear','#2c7775')]:
    x,y=t(M['information'][a]);b+=circle(x,y,10,c,'white',2)
for key,c,dash in [('partial_view_target','#b67e25',''),('blocked_target','#923f51','6 5')]:
    b+=path([t(M['information']['street_witness']),t(M['information'][key])],'none',c,3,False,dash)
b+=path([t(M['information']['bar_speaker']),t(M['information']['overhear'])],'none','#2c7775',5,False,'2 6')
b+=text(65,195,'WEST / street observer',22,weight=700)+text(70,1060,'EAST / rear doors to yard',22,weight=700)
b+=text(620,260,'PARTIAL KNOWLEDGE',25,weight=700)
rows=['Ochre: a potential view of','front-room handling through','the shop window.','','Red: the same observer’s','line to a hand in the snug','meets the 1.45 m screen.','','A standing head may remain','visible above that screen.','It is not total concealment.','','Teal: the overhearing seat.','Bar voices might reach it;','the screen is not a sound wall.','','Curtains, reflections, light,','pose, recognition and timing','all need live testing.']
for i,row in enumerate(rows):b+=text(620,300+i*31,row,20,MUTED)
b+=text(65,1120,'Morning delivery / lunch regulars / evening return: authored meeting intentions.',18,MUTED)
b+=text(65,1155,'A sightline or nearby seat does not guarantee witnessing, memory or dialogue.',18,MUTED)
save('mickeys-gameplay',1060,1250,b,"Mickey's / what can be known",'DESIGN INTENT / NOT A PERCEPTION OR ACOUSTIC TEST')
print('Wrote local gameplay drawing.')
