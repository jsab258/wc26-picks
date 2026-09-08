"""Deterministic authored drawings. Python standard library; no procedural layout."""
from pathlib import Path
import json, html, math, base64
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'previews'; OUT.mkdir(exist_ok=True)
A=json.loads((ROOT/'data/atlas.json').read_text())
from pub_geometry import geometry, resolved, plan_boxes, digest
M=resolved(json.loads((ROOT/'data/mickeys.json').read_text()))
INK='#253a3d'; BG='#f5f0e5'; MUTED='#607073'
def esc(s): return html.escape(str(s))
def text(x,y,s,size=20,fill=INK,anchor='start',weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'
def line(x1,y1,x2,y2,stroke=INK,w=2,dash=''):
    return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{stroke}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def rect(x,y,w,h,fill,stroke='none',sw=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def path(pts,fill='none',stroke=INK,w=2,close=False,dash=''):
    p='M'+' L'.join(f'{x},{y}' for x,y in pts)+(' Z' if close else '')
    return f'<path d="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def circle(x,y,r,fill,stroke='none',sw=1): return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def save(name,w,h,body,title,subtitle='ART PROPOSAL / OWNER VISUAL APPROVAL PENDING'):
    head=rect(0,0,w,h,BG)+text(38,43,'LEDGER  /  ATLAS 01',17,MUTED,weight=700)+text(38,94,title,40,weight=700)+text(38,125,subtitle,16,MUTED)+line(38,147,w-38,147,'#b9beb3')
    foot=line(38,h-52,w-38,h-52,'#b9beb3')+text(38,h-22,'MERIDIAN  /  1988-1992',15,MUTED)+text(w-38,h-22,'AUTHORED DESIGN',15,MUTED,'end')
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{head}{body}{foot}</svg>'
    (OUT/(name+'.svg')).write_text(svg,encoding='utf-8')
def town(overlay=False):
    def t(p): return (50+p[0]*.8,190+(1020-p[1])*.8)
    b=rect(38,174,904,710,'#dedbcb')
    coast=A['land'][:A['land'].index([1040,1000])+1]
    b+=path([t(p) for p in coast]+[(942,884),(38,884),(38,t(coast[0])[1])],'#b9d3d2','none',0,True)
    b+=path([t(p) for p in A['land']],BG,INK,2,True)
    for i,d in enumerate(A['districts']):
        b+=path([t(p) for p in d['polygon']],d['colour'],'#f5f0e5',2,True)
    for c in A['contours']:
        b+=path([t(p) for p in c['points']],'none','#536e51',1.5,False,'4 5')
        x,y=t(c['points'][0]);b+=text(x+4,y-4,str(c['height'])+'m',13,'#35513e')
    for name,e,n,w,h in A['blocks']:
        x,y=t((e,n+h));b+=rect(x,y,w*.8,h*.8,'#f5f0e5','#536165',.7)
    for r in A['routes']:
        pts=[t(p) for p in r['points']]
        if r['kind']=='main': b+=path(pts,'none','#796f5b',11)+path(pts,'none','#fff6df',8)
        elif r['kind']=='minor':b+=path(pts,'none','#fff6df',4)
        else:b+=path(pts,'none','#f5edcf',3,False,'4 4')
    b+=path([t(p) for p in A['rail']['points']],'none','#4b5350',3,False,'8 5')
    if not overlay:
        for q in A.get('map_labels',[]):
            x,y=t(q['point']);b+=text(x,y,q['text'],14,INK)
    for d in A['districts']:
        x,y=t(d['label']);num=A['districts'].index(d)+1
        b+=circle(x,y,18,INK)+text(x,y+6,num,18,'white','middle',700)
    if overlay:
        for r in A['gameplay']['daily']:b+=path([t(p) for p in r['points']],'none','#e68b29',5)
        for r in A['gameplay']['escape']:b+=path([t(p) for p in r['points']],'none','#00565d',4,False,'6 4')
        for e,n,ee,nn in A['gameplay']['witness']:
            b+=path([t((e,n)),t((ee,nn))],'none','#923f51',3,False,'3 3')
        for p in A['gameplay']['phones']:
            x,y=t(p);b+=rect(x-6,y-6,12,12,'#a73540','#fff',1)
    for l in A['landmarks']:
        x,y=t(l['point']);b+=circle(x,y,4,INK)
        if l['venue']:b+=circle(x,y,9,'none',INK,1)
    if not overlay:
        for label,point in [('Retort works',[75,355]),('Market Hall',[385,680]),('School gate',[185,820]),('Records Court',[765,883]),('Police',[858,931]),('Tivoli',[748,510]),('Winter Rooms',[844,479]),('Harbour Board',[478,391])]:
            x,y=t(point);b+=rect(x-4,y-15,len(label)*7.7+8,20,BG)+text(x,y,label,14,INK,weight=700)
    # Annotated source street magnifier: too small for phone otherwise.
    x,y=t([400,371]);b+=circle(x,y,18,'none','#fff',3)+line(x+18,y,690,795,'white',2)
    b+=rect(686,776,230,64,INK)+text(703,802,"MICKEY'S STREET",18,'#fff',weight=700)+text(703,826,'See Hook detail',17,'#dae3d8')
    b+=text(306,840,'BASIN',15,INK)+text(765,860,'OPEN SEA',18,INK)
    b+=text(50,166,'INLAND STUDY EXTENT',12,MUTED)
    b+=line(902,243,902,194,INK,3)+path([[894,205],[902,192],[910,205]],INK,INK,1,True)+text(902,183,'N',17,INK,'middle',700)
    b+=line(70,865,230,865,INK,4)+text(70,855,'0',14)+text(230,855,'200 m',14,anchor='end')
    for i,d in enumerate(A['districts']):
        col=i%2;row=i//2;x=45+col*465;y=930+row*62
        b+=circle(x+17,y,17,d['colour'])+text(x+17,y+6,i+1,17,INK,'middle',700)+text(x+45,y-2,d['name'],32,weight=700)+text(x+45,y+22,d['role'],18,MUTED)
    if overlay:
        y=1190;b+=line(50,y,105,y,'#e68b29',5)+text(115,y+6,'Daily routes',18)
        b+=line(335,y,390,y,'#00565d',4,'6 4')+text(400,y+6,'Escape intention',18)
        b+=line(665,y,720,y,'#923f51',3,'3 3')+text(730,y+6,'Possible view',18)
        b+=text(45,1238,'Ring = information venue   /   red square = phone',17,MUTED)
        b+=text(45,1266,'Routes, sightlines and timing are not simulation results.',17,MUTED)
        h=1360
    else:
        b+=text(45,1190,'Pale blocks: authored massing  /  dashed green: elevation',17,MUTED)
        b+=text(45,1220,'Circle: information venue  /  solid pale line: main route',17,MUTED)
        h=1320
    save('gameplay-overlay' if overlay else 'atlas-overview',980,h,b,'How the town talks' if overlay else 'MERIDIAN', 'DESIGN INTENT / NOT SIMULATED' if overlay else 'SEVEN DISTRICTS / ONE WORKING TOWN')
def hook():
    # Exact source-frame local plan. North is upward, source +z east/right.
    s=15;cx=450;yy=930
    def t(x,z):return cx+z*s,yy-x*s
    b='';
    for z0,z1,col in [(-3,3,'#838b88'),(3.125,5.125,'#d5cdb9'),(-5.125,-3.125,'#d5cdb9')]:
        x,y=t(42,z0);b+=rect(x,y,(z1-z0)*s,42*s,col)
    for name,x0,bays in [('west_south',3,3),('west_north',24,3),('east_parade',3,6)]:
        z0=5.125 if name=='east_parade' else -13.125
        for i in range(bays):
            u,v=t(x0+(i+1)*6,z0);col='#995746' if name=='east_parade' and i==0 else '#b5aea0'
            b+=rect(u,v,8*s,6*s,col,INK,1.5)
            label="MICKEY'S" if name=='east_parade' and i==0 else ('Fish shop' if name=='east_parade' and i==1 else str(i))
            b+=text(u+60,v+49,label,17,'white' if i==0 and name=='east_parade' else INK,'middle',700)
    # Proposed authored rear lane, WC and private yard.
    u,v=t(9,13.125);b+=rect(u,v,6*s,6*s,'#dbc9a4',INK,1.5)
    u,v=t(5.2,13.125);b+=rect(u,v,2.6*s,2.2*s,'#af8366',INK)
    u,v=t(12,19.125);b+=rect(u,v,2.4*s,15*s,'#e8dfc9',INK)
    u,v=t(3,5.125);b+=rect(u,v,14*s,3*s,'#e8dfc9',INK)
    b+=text(450,970,'SOUTH: Old Basin / Harbour Board',22,anchor='middle',weight=700)
    b+=text(450,218,'NORTH: Copper Row / market',22,anchor='middle',weight=700)
    b+=path([[450,285],[450,235]],'none',INK,3)+text(470,260,'N',18,weight=700)
    b+=text(54,1010,'Quay Street',32,weight=700)+text(54,1040,'42 m source segment, extended into the town by proposal',18,MUTED)
    for i,(a,c) in enumerate([('6 m carriageway','2 m footway each side'),('3 m west yard gap','Source x = 21 to 24'),('Mickey’s: east bay 0','6 m frontage × 8 m depth')]):
        x=54+i*300;b+=text(x,1090,a,20,weight=700)+text(x,1118,c,17,MUTED)
    # labels kept outside geometry and leaders disjoint
    b+=text(50,565,'West yard',20,weight=700)+text(50,590,'3 m entrance',17,MUTED)+line(190,578,250,592)
    b+=text(680,695,'East terrace',20,weight=700)+text(680,720,'6 × 6 m bays',17,MUTED)+line(674,708,650,710)
    b+=text(794,807,'Rear lane',20,weight=700)+text(794,834,'2.4 m',17,MUTED)+line(805,844,766,875)
    b+=text(54,1180,'Source IDs and coordinates are preserved in data/atlas.json.',17,MUTED)
    b+=text(54,1208,'Yard, lane and wider connections are authored proposals.',17,MUTED)
    save('hook-detail',980,1320,b,'The Hook / first street','SOURCE GEOMETRY + PROPOSED CONNECTIONS')
def dim(x1,y1,x2,y2,label):
    return line(x1,y1,x2,y2,'#667578',1)+line(x1-5,y1-5,x1+5,y1+5,'#667578',1)+line(x2-5,y2-5,x2+5,y2+5,'#667578',1)+text((x1+x2)/2,(y1+y2)/2-8,label,17,MUTED,'middle')
def plan(upper=False):
    s=90;ox=80;oy=280;sh=M['shell'];w=sh['width'];d=sh['depth']
    def box(a,col,stroke=INK):u,v,ww,dd=a;return rect(ox+u*s,oy+v*s,ww*s,dd*s,col,stroke,1)
    b=text(80,196,'WEST / QUAY STREET',20,weight=700)+text(690,196,'NORTH →',20,weight=700)
    b+=box([0,0,w,d],'#e9e0cf')
    rooms=M['upper_rooms'] if upper else M['ground_zones']
    for r in rooms:b+=box(r['box'],r['colour'],'none')
    if upper:b+=box(M['stairs']['floor_void'],'#8c938d')
    colours={'brick':INK,'plaster':'#686d64','wood':'#886146','cloth':'#a57a75','glass_proxy':'#83b4bb','maroon':'#602f34','metal':'#5c6a68'}
    for g in plan_boxes(M,upper):
        u,v,ww,dd=g['box']
        # The yard has its own sheet. Retain open leaves at the facade.
        if u<0 or u>=w or v>=d or v+dd<0:continue
        projected=box(g['box'],colours.get(g['material'],'#d5c5a8'))
        b+=f'<g id="geom-{g["id"]}" data-box="'+','.join(str(round(x,6)) for x in g['box'])+'">'+projected+'</g>'
    b+=f'<metadata id="geometry-digest">{digest(M)}</metadata>'
    b+=dim(ox,oy-45,ox+w*s,oy-45,f'{w:.2f} m source frontage')
    b+=line(ox-30,oy,ox-30,oy+d*s,MUTED,1)+text(ox-35,oy+d*s/2,f'{d:g} m',16,MUTED,'end')
    if upper:
        for r in rooms:
            u,v,ww,dd=r['box'];x=ox+(u+ww/2)*s;y=oy+(v+.32)*s
            b+=text(x,y,r['name'],17,anchor='middle',weight=700)+text(x,y+20,f'{ww:.3f} × {dd:.3f} m',13,MUTED,'middle')
        b+=text(ox+.68*s,oy+3.2*s,'VOID',16,'white','middle')
        notes=['Private household','Walls and furniture','follow authored room edges.','','Bedroom / living room','Book room / kitchen / bath','','No customer access','No invented room solver','','Door gaps: 0.70 m','Upper level: +'+str(sh['ground_floor_height'])+' m','','Stair, leaf poses and','headroom await Blender','and navigation review.']
    else:
        for r in rooms:
            if r['id'] in ['public','store','rear_passage','snug','counter']:
                u,v,ww,dd=r['box'];b+=text(ox+(u+ww/2)*s,oy+(v+dd/2)*s,r['name'],16,anchor='middle',weight=700)
        p=M['information']['overhear'];b+=circle(ox+p[0]*s,oy+p[1]*s,13,'#d3a447',INK)+text(ox+p[0]*s,oy+p[1]*s+5,'O',15,anchor='middle')
        for key,col in [('customer','#c37c21'),('staff','#2a8179')]:b+=path([(ox+u*s,oy+v*s) for u,v in M['paths'][key] if -.2<=v<=d],'none',col,4,False,'8 5')
        st=M['stairs'];notes=['Public door: 0.90 m','Private door: 0.838 m','','O  Overhearing nook','Screen: 1.45 m','','Rear beer-store proposal','Public / staff rear doors','','Private stair: '+str(st['width'])+' m',str(st['risers'])+' risers / '+str(st['goings'])+' goings','Going: '+str(st['going'])+' m','','Outward private leaf','conflicts with footway.','Review access detail.','','Yard WC on site sheet.']
    for i,n in enumerate(notes):b+=text(695,300+i*29,n,19,MUTED)
    b+=text(80,1050,'EAST / REAR YARD',20,weight=700)
    b+=text(80,1090,'Shared geometry commands drive this plan and the unexecuted Blender adapter.',16,MUTED)
    save('mickeys-upper' if upper else 'mickeys-ground',1060,1190,b,"Mickey's / upper floor" if upper else "Mickey's / ground floor",'DIMENSIONED AUTHORING PLAN / METRES')

def elevations():
    b='';s=74;sh=M['shell'];ew=sh['width'];eh=sh['ground_floor_height']+sh['upper_height'];ridge=eh+sh['depth']/2*math.tan(math.radians(sh['roof_pitch_deg']))
    for rear,ox in [(False,65),(True,620)]:
        oy=1000;W=ew*s
        def ex(u,w=0): return ox+((u if rear else ew-u-w)*s)
        b+=text(ox,203,'REAR / EAST' if rear else 'FRONT / WEST',25,weight=700)
        b+=rect(ox,oy-eh*s,W,eh*s,'#9a6450',INK,2)
        b+=rect(ox-22,oy-ridge*s,W+44,(ridge-eh)*s,'#556160',INK,2)
        for rh in [6.7,7.2,7.7,8.2,8.7]:b+=line(ox-20,oy-rh*s,ox+464,oy-rh*s,'#7a8581',1)
        b+=rect(ox+25,oy-9.8*s,35,1.25*s,'#82543f',INK)+rect(ox+370,oy-9.8*s,35,1.25*s,'#82543f',INK)
        for op in M['upper_openings']:
            if op['side']==('rear' if rear else 'front'):b+=rect(ex(op['start'],op['width']),oy-(sh['ground_floor_height']+op['sill']+op['height'])*s,op['width']*s,op['height']*s,'#9fb2b0',INK,5)
        if rear:
            for op in M['openings']:
                if op['side']=='rear':b+=rect(ox+op['start']*s,oy-op['height']*s,op['width']*s,op['height']*s,'#485a4f',INK,2)
            b+=rect(ox,oy-2.55*s,2.2*s,2.55*s,'#b18c6d',INK,2)
            b+=rect(ox-.05*s,oy-2.68*s,2.3*s,.13*s,'#575f5d',INK)
            b+=text(ox+15,oy+30,'1958 WC addition / repaired rear brick',16,MUTED)
        else:
            b+=rect(ox,oy-3.4*s,W,.55*s,'#602f34',INK)
            b+=text(ox+222,oy-3.03*s,"MICKEY'S",27,'#ead5aa','middle',700)
            for op in M['openings']:
                if op['side']!='front':continue
                sill=op.get('sill',0);col='#829e9a' if op['id']=='front_glass' else '#5f3035'
                b+=rect(ex(op['start'],op['width']),oy-(sill+op['height'])*s,op['width']*s,op['height']*s,col,INK,2)
            b+=text(ox+15,oy+30,'Two source door positions retained',16,MUTED)
        b+=line(ox-10,oy,ox+W+10,oy,INK,3)+dim(ox,oy+65,ox+W,oy+65,'6.00 m')
    b+=text(65,1120,'Source shell: floor +0.10 m / upper +3.50 m / eaves +6.30 m / ridge +9.10 m',19,weight=700)
    b+=text(65,1155,'Levels above street crown. Roof envelope: 8 m depth at 35°. Glazing and trim are proposals.',17,MUTED)
    save('mickeys-elevations',1150,1250,b,"Mickey's / front and rear",'DRAWN ELEVATIONS / NOT RENDERED GEOMETRY')
def yard():
    s=57;ox=240;oy=390
    def t(u,v):return ox+u*s,oy+v*s
    b=rect(ox,oy,6*s,8*s,'#b98774',INK,2)+text(ox+171,oy+230,"MICKEY'S",27,INK,'middle',700)
    b+=rect(ox,oy+8*s,6*s,6*s,'#d9c8a6',INK,2)+rect(ox,oy+8*s,2.2*s,2.6*s,'#b78f73',INK,2)
    b+=text(ox+1.1*s,oy+9.4*s,'WC',24,INK,'middle',700)
    b+=rect(ox-3*s,oy+14*s,12*s,2.4*s,'#e5dfcc',INK,1)
    b+=rect(ox-3*s,oy-2*s,9*s,2*s,'#e5dfcc',INK,1)
    b+=rect(ox-3*s,oy-2*s,3*s,16*s,'#d2c7b0',INK,1)
    for k,col in [('escape','#1d666d'),('delivery','#cf8c28')]:b+=path([t(u,v) for u,v in M['paths'][k]],'none',col,4,False,'8 5')
    b+=line(*t(4.6,14),*t(5.8,14),'#f5f0e5',10)+text(ox+245,oy+14*s-16,'1.2 m gate',17)
    b+=text(690,255,'A second way out',28,weight=700)
    notes=['Yard: 6 × 6 m','Rear lane: 2.4 m','WC: 2.2 × 2.6 m','','Gate to rear lane; turn','south, then west along','the terrace-end passage','back to Quay Street.','','Beer arrives by trolley.','A delivery van stays at','the wider basin route.','','No route crosses a','neighbouring interior.','','Yard wall: 1.8 m','Upper windows overlook','much of the yard.','This is not invisible cover.']
    for i,n in enumerate(notes):b+=text(690,300+i*29,n,19,MUTED)
    b+=text(690,940,'TEAL: escape intention',19,'#1d666d')+text(690,974,'OCHRE: delivery',19,'#aa7424')
    b+=text(80,1380,'Rear lane runs behind the terrace. Return passage is south of bay 0.',18,MUTED)
    b+=text(50,1420,'Plan orientation: up = west / right = north. Atlas north-up connections are in Hook detail.',17,MUTED)
    save('mickeys-yard',1120,1510,b,"Mickey's / service and escape",'AUTHORING PLAN / ROUTES NOT WALK-TESTED')
def district_details():
    for i,d in enumerate(A['districts']):
        x0=min(p[0] for p in d['polygon']);x1=max(p[0] for p in d['polygon']);n0=min(p[1] for p in d['polygon']);n1=max(p[1] for p in d['polygon'])
        s=min(730/(x1-x0),590/(n1-n0));ox=70;oy=200
        def t(p):return ox+(p[0]-x0)*s,oy+(n1-p[1])*s
        b=path([t(p) for p in d['polygon']],d['colour'],INK,2,True)
        prefix={'hook':'H','copper':'C','exchange':'E','parade':'P','fairview':'F','ironside':'I','gullwing':'G'}[d['id']]
        if d['id']=='hook':
            b+=path([t(p) for p in [[300,240],[385,240],[385,220],[440,220],[440,280],[300,280]]],'#b9d3d2','none',0,True)
        for name,e,n,w,h in A['blocks']:
            if name.startswith(prefix):
                x,y=t((e,n+h));b+=rect(x,y,w*s,h*s,'#efe7d5','#5e6864',1)
        for r in A['routes']:
            # clip all route geometry to district polygon
            pts=[t(p) for p in r['points']]
            clip=f'<clipPath id="dc{r["id"]}"><path d="M'+ ' L'.join(f'{x},{y}' for x,y in [t(p) for p in d['polygon']])+' Z"/></clipPath>'
            route_draw=path(pts,'none','#fff4dc',6 if r['kind']=='main' else 3,False,'4 4' if r['kind']=='foot' else '')
            water_route=(r['id']=='dockfoot' and d['id']=='hook') or (r['id']=='pier' and d['id']=='gullwing')
            b+=route_draw if water_route else clip+f'<g clip-path="url(#dc{r["id"]})">'+route_draw+'</g>'
        for l in A['landmarks']:
            if l['district']==d['id']:
                x,y=t(l['point']);b+=circle(x,y,8,INK)
                if l['id']=='G1':b+=text(x-16,y-16,'Winter Rooms',21,anchor='end',weight=700)
                elif l['id']=='G2':b+=text(x+16,y+38,'Short pier',21,weight=700)
                else:b+=text(x+16,y-10,l['name'],21,weight=700)
        for q in A.get('map_labels',[]):
            if q.get('district')==d['id']:
                x,y=t(q['point']);b+=text(x,y,q['text'],19,INK,weight=700)
        b+=line(70,821,70+100*s,821,INK,3)+text(70,810,'100 m',17,MUTED)
        b+=text(70,860,d['role'],30,weight=700)+text(70,900,f"Proposed relief: {d['height_m'][0]} to {d['height_m'][1]} m",20,MUTED)
        for j,(name,c) in enumerate(d['materials']):
            x=70+j*198;b+=rect(x,940,175,70,c)+text(x,1040,name,18,MUTED)
        b+=text(70,1115,'Objects: '+', '.join(d['objects'][:2]),18,MUTED)+text(70,1145,', '.join(d['objects'][2:]),18,MUTED)
        b+=line(848,280,848,220,INK,3)+text(848,205,'N',20,INK,'middle',700)
        b+=text(70,1205,'See matching concept sheet. Landmarks and terrain share atlas coordinates.',16,MUTED)
        save('district-'+d['id']+'-plan',900,1300,b,d['name'],'DISTRICT DETAIL / PROPOSED MATERIALS')
if __name__=='__main__':
    town();town(True);hook();plan();plan(True);elevations();yard();district_details()
    print('Wrote 14 SVG drawings from authored coordinates.')
