"""Authored continuation sheets. Reads the existing atlas and operational decisions."""
from draw import *
O=json.loads((ROOT/'data/pub-operations.json').read_text(encoding='utf-8'))
def words(x,y,lines,size=20,col=MUTED):return ''.join(text(x,y+i*(size+9),s,size,col) for i,s in enumerate(lines))
def economy():
 def t(p):return 50+.8*p[0],190+.8*(1020-p[1])
 b=path([t(p) for p in A['land']], '#e1dccc',INK,2,True)
 for d in A['districts']:b+=path([t(p) for p in d['polygon']],d['colour'],BG,2,True)
 for r in A['routes']:b+=path([t(p) for p in r['points']],'none','#fff4dc',5 if r['kind']=='main' else 2)
 for j,f in enumerate(A['working_town']['flows']):
  b+=path([t(p) for p in f['points']],'none',['#075a62','#e6a234','#843945','#3b4e9b'][j],4)
  x,y=t(f['points'][0]);b+=circle(x,y,13,INK)+text(x,y+5,j+1,16,'white','middle')
 for d in A['districts']:
  x,y=t(d['label']);b+=text(x,y-23 if d['id']=='exchange' else y,d['name'],18,INK,'middle',700)
 for q in A['working_town']['boundaries']:b+=path([t(p) for p in q['points']],'none','#b42d43',5,False,'4 3')
 b+=text(560,177,'NORTH: STATION / SHOPS',18,weight=700)+text(45,426,'← FREIGHT ROAD',17,weight=700)
 b+=text(300,882,'Small craft here; deep berths beyond west edge',18,weight=700)
 for j,f in enumerate(A['working_town']['flows']):b+=text(50,948+j*48,f'{j+1}   '+f['name'],24,weight=700)
 b+=words(50,1160,['Coloured lines: authored daily journeys. Red dashes: work gates.','District colour and coastline match the original atlas. North is up.','All times, employers, access and sightlines await simulation.'],18)
 save('town-work-and-home',980,1330,b,'Work, homes and meetings','SAME ATLAS / FICTIONAL EMPLOYERS AND ROUTES / NOT SIMULATED')
def changes():
 b=''
 # Three original diagrams; archive images are linked, not replicated.
 b+=text(48,200,'01 / A working shopfront, not frozen heritage',26,weight=700)
 b+=rect(55,235,370,250,'#a27662',INK)+rect(70,330,340,42,'#36565d')+text(240,360,'QUAY STORES',26,'#eee1bc','middle',700)
 for x in [80,166,252,338]:b+=rect(x,245,55,64,'#c6d5d0',INK)
 b+=rect(75,380,235,91,'#b4cbc5',INK)+rect(318,380,77,105,'#bed3cf',INK)
 for j in range(6):b+=rect(82+j*35,436,25,20,'#b59366',INK)
 b+=words(465,260,['R05: Princes Avenue, Hull, 1989','Metal frame + fluorescent strips','Goods near glass, tiled stallriser','D01: grocery in existing bay 2','The source shell stays in place.'],20)
 b+=text(48,550,'02 / Fairview includes ordinary occupied flats',26,weight=700)
 for i in range(3):
  x=55+i*125;b+=rect(x,585,118,210,'#bbb5a2',INK)+rect(x+10,610,90,62,'#617b7e')+rect(x+5,670,106,8,'#e4d9c8')+rect(x+10,727,90,63,'#71878b')
  for j in range(6):b+=line(x+10+j*17,680,x+10+j*17,710,INK,2)
 b+=line(65,818,410,818,INK)+rect(125,818,45,43,'#9b7b7e')+rect(240,818,60,30,'#e8dbc1')
 b+=words(465,610,['R07: Newtown Square, Hull, 1989','Balcony, washing, grass court','D03: Foundry Court lower slope','R11: stepped Plymouth lanes','Retain upper villas and 45m crest.'],20)
 b+=text(48,945,'03 / Rear space does a job',26,weight=700)
 b+=rect(65,990,350,140,'#ddd0b6',INK)+rect(80,1005,65,85,'#b1917f',INK)+text(112,1050,'WC',20,anchor='middle')
 b+=rect(330,1020,58,80,'#929e90',INK)+text(210,1080,'YARD',23,anchor='middle')+path([[405,1145],[210,1145],[210,1100]],'none','#247c78',5)
 b+=words(465,992,['R12/R15: service work matters','D08: receiving + returns + washing','No invented cellar below street','D09: waste choice is municipal,','not a blanket period prohibition.'],20)
 b+=words(48,1210,['Original SVG interpretations; source observations and rights: references/CONTINUATION.md.','These details qualify the existing concepts; no new photoreal render is claimed.'],17)
 save('evidence-revisions',980,1340,b,'What the evidence changes','DRAWN DESIGN STUDIES / NOT PHOTOGRAPHS OR GENERATED CONCEPTS')
def services():
 b=text(48,200,'A / Retained room: capacity study',27,weight=700);s=210;ox=60;oy=260
 st=O['beer_store'];u,v,w,d=st['room_box'];b+=rect(ox,oy,w*s,d*s,'#e6decf',INK,3)
 for k,col in [('stillage_box','#8daba2'),('reserve_box','#baa78b')]:
  x,y,ww,dd=st[k];b+=rect(ox+(x-u)*s,oy+(y-v)*s,ww*s,dd*s,col,INK)
  for j in range(2):b+=rect(ox+(x-u+.045)*s,oy+(y-v+.045+j*.55)*s,.41*s,.49*s,'#adb7b1',INK)
 b+=text(ox+w*s/2,oy-18,f'{w:.3f} m',20,anchor='middle')+text(245,oy+260,'0.67m',21,anchor='middle')
 b+=words(505,260,['One cask line; two stillaged casks','(serving + settling), two reserves.','Modern comparator: 0.41 × 0.49m','per cask, R21; not a period model.','','Cooling unit / drainage / tap reach','still require detailed resolution.','Centre aisle is a space allowance,','not a trolley or handling test.'],21)
 b+=words(60,740,['Delivery → rear door → store, before opening. Empty returns leave the same way.','R13 documents an unusual ground-floor cellar in 2013; R15 explains the work.'],18)
 b+=text(48,850,'B / Basement: unadopted',26,weight=700)+text(505,850,'C / Yard room: unadopted',26,weight=700)
 b+=rect(70,890,330,70,'#b88a6c',INK)+rect(120,960,235,110,'#859a94',INK)+path([[100,950],[160,980],[220,1005],[280,1040]],'none',BG,9)
 b+=rect(525,900,330,160,'#e1d2b8',INK)+rect(535,910,95,70,'#aa8570',INK)+rect(735,910,105,140,'#859a94',INK)
 b+=words(60,1110,['Requires cellar stair, structure,','delivery drop and drainage.','None established by source.'],20)+words(505,1110,['Takes usable yard and adds a','longer insulated beer-line run.','Conflicts with WC/escape review.'],20)
 b+=text(48,1240,'The private-door/stair conflict is separate: see mickeys-access.png.',18)
 save('mickeys-service-options',980,1340,b,'Mickey’s / behind the bar','OPERATIONAL DESIGN STUDY / NO SOURCE ANCHOR MOVED')
def uses():
 b=text(50,200,'Existing 42m source street / north ↑',25,weight=700)
 s=12;cx=470;yy=810
 b+=rect(cx-36,yy-42*s,72,42*s,'#92998f')
 for i,row in enumerate(O['neighbours']):
  id,name,use,rear=row
  if id.startswith('east'):j=int(id[-1]);x=cx+5.125*s;n=3+j*6
  else:j=int(id[-1]);x=cx-13.125*s;n=(3 if 'south' in id else 24)+j*6
  b+=rect(x,yy-(n+6)*s,8*s,6*s,'#9a6756' if i==0 else '#d5c3a1',INK)+text(x+48,yy-(n+3)*s+7,i+1,22,anchor='middle',weight=700)
 b+=path([[cx,yy-1.5*s],[cx+20.325*s,yy-1.5*s],[cx+20.325*s,yy-12*s]],'none','#227b78',16)
 b+=words(65,360,['West court:','chandler receiving,','launderette repairs,','household access.','','Court is not a','random escape gap.'],20)
 b+=words(740,540,['Pub lane:','WC / empties /','trolley access.','Ends at neighbour’s','service boundary.'],18)
 b+=text(50,860,'Uses are proposals; IDs, orientations and dimensions remain unchanged.',18)
 for i,row in enumerate(O['neighbours']):
  x=50+(i//6)*460;y=925+(i%6)*62;b+=text(x,y,f'{i+1:02d}   {row[1]}',25,weight=700)+text(x,y+24,row[0],16,MUTED)
 b+=text(50,1330,'Upper households and rear uses: data/pub-operations.json. Interior inventories remain to author.',16)
 save('hook-uses',980,1440,b,'The Hook / who uses each door','AUTHORED USES / SOURCE STREET RETAINED / NOT LIVE SCENE DATA')
if __name__=='__main__':economy();changes();services();uses();print('Four continuation sheets')
