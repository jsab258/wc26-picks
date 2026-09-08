"""Mutation regressions for the real plan renderer and Blender input commands.
No bpy execution: this cannot test Blender API compatibility or rendered meshes.
"""
import copy, json, tempfile, xml.etree.ElementTree as ET
from pathlib import Path
import draw
from pub_geometry import geometry, digest, headroom, resolved

R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/mickeys.json').read_text());checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
def boxes(d):return {b['id']:b for b in geometry(d)['boxes']}
def render(d,upper):
    with tempfile.TemporaryDirectory(prefix='atlas-plan-') as tmp:
        previous=draw.OUT;draw.OUT=Path(tmp);draw.M=resolved(d)
        try:
            draw.plan(upper)
            return ET.parse(draw.OUT/('mickeys-upper.svg' if upper else 'mickeys-ground.svg'))
        finally:draw.OUT=previous;draw.M=resolved(D)
def plan_box(tree,id):
    return [float(v) for v in next(e for e in tree.iter() if e.get('id')=='geom-'+id).get('data-box').split(',')]
def eq(a,b):return all(abs(x-y)<1e-6 for x,y in zip(a,b))

base=boxes(D)
check('Retained first and final tread rise and position',eq(base['stair_tread_00']['box'],[.24,.3,.8,.24]) and abs(base['stair_tread_17']['height']-18*3.4/19)<1e-9)
check('Retained upper bed is now room-relative geometry',eq(base['bed']['box'],[3.7,.55,1.4,2]))
check('Both real plan sheets match current model commands',all(eq(plan_box(render(D,upper),id),base[id]['box']) for upper,id in [(False,'counter'),(True,'bed')]))
changed=copy.deepcopy(D);changed['stairs']['going']=.25
check('Going mutation changes final model tread and real SVG together',eq(plan_box(render(changed,False),'stair_tread_17'),boxes(changed)['stair_tread_17']['box']) and not eq(boxes(changed)['stair_tread_17']['box'],base['stair_tread_17']['box']))
changed=copy.deepcopy(D);changed['upper_rooms'][0]['box'][0]+=.1
check('Room move controls upper wall AND bed in model',abs(boxes(changed)['bed']['box'][0]-base['bed']['box'][0]-.1)<1e-9 and abs(boxes(changed)['bed_hall_0_0']['box'][0]-base['bed_hall_0_0']['box'][0]-.1)<1e-9)
check('Room move controls real upper drawing',eq(plan_box(render(changed,True),'bed'),boxes(changed)['bed']['box']))
check('Stale plan/model divergence is exposed after room move',not eq(plan_box(render(D,True),'bed'),boxes(changed)['bed']['box']) and digest(D)!=digest(changed))
changed=copy.deepcopy(D);changed['partitions'][0]['thickness']=.16
check('Store partition thickness mutation reaches both outputs',eq(plan_box(render(changed,False),'store_top_0_0'),boxes(changed)['store_top_0_0']['box']) and boxes(changed)['store_top_0_0']['box'][3]==.16)
changed=copy.deepcopy(D);changed['stairs']['floor_void'][1]+=.25
check('Headroom responds to actual floor void mutation',headroom(changed)<headroom(D))
changed=copy.deepcopy(D);changed['shell']['floor_thickness']+=.1
check('Headroom responds to actual slab thickness',abs(headroom(changed)-headroom(D)+.1)<1e-9)
changed=copy.deepcopy(D);changed['openings'][0]['start']=100
try:geometry(changed);rejected=False
except ValueError:rejected=True
check('Opening outside shell is rejected, not silently clamped',rejected)
recipe=(R/'recipes/mickeys_blockout.py').read_text()
check('Blender adapter consumes shared commands and records their digest',"G=geometry(D)" in recipe and "for b in G['boxes']" in recipe and "'geometry_sha256':digest(D)" in recipe)
report={'kind':'12 Python mutation/source checks; NOT Blender execution','count':len(checks),'passed':checks,'untested':['Blender API, mesh/render agreement, leaf poses, stair traversal, navmesh, acoustics, regulations']}
(R/'verification-recipe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
