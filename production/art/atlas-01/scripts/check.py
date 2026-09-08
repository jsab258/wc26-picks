"""Commission invariants. Arithmetic/2D checks only, never a game or Blender run."""
from pathlib import Path
import json,math,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];REPO=R.parents[2]
A=json.loads((R/'data/atlas.json').read_text());M=json.loads((R/'data/mickeys.json').read_text())
B=json.loads((REPO/'production/specs/vignette-bill-of-materials.json').read_text())
P=json.loads((REPO/'production/specs/vignette-pieces.json').read_text())
S=json.loads((REPO/'production/specs/vignette-scene.json').read_text())
from pub_geometry import resolved, headroom
M=resolved(M)
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def intersects(a,b,r):
    x,y,w,h=r;t0=0;t1=1;dx=b[0]-a[0];dy=b[1]-a[1]
    for p,q in [(-dx,a[0]-x),(dx,x+w-a[0]),(-dy,a[1]-y),(dy,y+h-a[1])]:
        if p==0:
            if q<0:return False
        else:
            t=q/p
            if p<0:t0=max(t0,t)
            else:t1=min(t1,t)
            if t0>t1:return False
    return True
def expanded(b,m):x,y,w,h=b;return [x-m,y-m,w+2*m,h+2*m]
def segments(ps):return zip(ps,ps[1:])
byname={p['name']:p for p in P['pieces']}
pub=byname[M['source_piece']]
check('Owner base and exact source pub shell retained',A['base_commit']=='7722b45cb3dcee2fbcee26675fae4fef641cbba7' and [pub[k] for k in ['x_m','y_m','z_m','sx_m','sy_m','sz_m']]==[6,3.2,9.125,6,6.2,8])
check('Street orientation and dimensions retained',A['street_anchor']['length_m']==S['street']['length_m']==42 and S['street']['carriageway']['half_width_m']*2==A['street_anchor']['carriageway_m']==6)
for o in M['openings']:
    if 'source' in o:
        p=byname[o['source']]
        check(o['id']+' retains source horizontal anchor and width',abs(3+o['start']+o['width']/2-p['x_m'])<1e-6 and o['width']==p['sx_m'])
check('Seven canonical districts, unique authored IDs',len(A['districts'])==7 and set(d['id'] for d in A['districts'])=={'hook','copper','exchange','parade','fairview','ironside','gullwing'})
check('Each district has a named information venue',all(any(l['district']==d['id'] and l['venue'] for l in A['landmarks']) for d in A['districts']))
check('Map streets clear authored massing by 5m half-corridor',not any(intersects(p,q,expanded(b[1:],5)) for b in A['blocks'] for r in A['routes']+[A['rail']] for p,q in segments(r['points'])))
solids=[(z['id'],z['box']) for z in M['ground_zones'] if z['id'] in ['counter','backbar','snug','store','stair']]+[(f['id'],f['box']) for f in M['furniture']]
for route in ['customer','staff','escape','delivery']:
    hits=[]
    for a,b in segments(M['paths'][route]):
        for name,box in solids:
            if route=='delivery' and name=='store':continue
            if intersects(a,b,expanded(box,.30)):hits.append(name)
    check(route+' path clears furniture at 0.30m radius',not hits)
    check(route+' avoids next east terrace bay',not any(intersects(p,q,[6,0,6,8]) for p,q in segments(M['paths'][route])))
check('Rear lane and south passage correctly used',all(u<6 or v>=14 for u,v in M['paths']['escape']) and [-1.5,15.2] in M['paths']['escape'])
check('19 risers reach source upper level',M['stairs']['risers']==19 and M['shell']['ground_floor_height']==3.4)
check('18 goings match authored stair run',math.isclose(M['stairs']['goings']*M['stairs']['going'],next(z['box'][3] for z in M['ground_zones'] if z['id']=='stair')))
min_head=headroom(M)
check('Simple under-floor headroom before void exceeds 2m',min_head>2)
observer=M['information']['street_witness'];target=M['information']['blocked_target']
screen=next(f for f in M['furniture'] if f['id']=='screen');sx,sy,sw,sd=screen['box'];eye=M['information']['eye_height'];hand=M['information']['target_hand_height']
t=(sy-observer[1])/(target[1]-observer[1]);u=observer[0]+t*(target[0]-observer[0]);h=eye+t*(hand-eye)
check('Illustrated hand sightline meets screen below top',sx<u<sx+sw and 0<h<screen['height'])
audit=json.loads((R/'data/assets.json').read_text());ids={x['id'] for x in B['items']}
check('All 77 existing BOM lines audited',len(ids)==77 and {x['id'] for x in audit['items'] if x['id_kind']=='existing BOM'}==ids)
check('New IDs are separate and all related BOM IDs resolve',all(x['id'] not in ids and all(y in ids for y in x['related_existing_bom_ids']) for x in audit['items'] if x['id_kind']!='existing BOM'))
check('Every asset has a picture and distinct engine status',all((R/x['thumbnail']).is_file() and x['engine_integration'] and x['basis'] for x in audit['items']))
check('Seven actual district concept files exist',all((R/'concepts'/f'{d["id"]}.png').is_file() for d in A['districts']))
svgs=list((R/'previews').glob('*.svg'))
for f in svgs:
    tree=ET.parse(f);seen=[x.attrib['id'] for x in tree.iter() if 'id' in x.attrib]
    check(f.name+' parses with unique SVG IDs',len(seen)==len(set(seen)))
for f in list((R/'scripts').glob('*.py'))+list((R/'recipes').glob('*.py')):compile(f.read_text(encoding='utf-8'),str(f),'exec')
check('All commission Python sources compile without running Blender',True)
report={'kind':'local arithmetic, source checks and SVG parsing; NOT runtime tests','passed':checks,'count':len(checks),'headroom_calculation_m':round(min_head,4),'hand_ray_at_screen':[round(u,4),3.3,round(h,4)],'bounds':'0.30m disk versus plan rectangles is a conservative furniture clearance check. It omits opening leaves, human poses, stairs traversal, navmesh, physics, acoustics and perception; these remain render/integration checks.'}
(R/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
