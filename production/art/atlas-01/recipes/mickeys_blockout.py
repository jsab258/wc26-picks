"""Atlas 01 spatial blockout. Run only in the studio's explicitly scheduled Blender lane.

blender --background --factory-startup --python production/art/atlas-01/recipes/mickeys_blockout.py -- --output-dir production/art/atlas-01/renders --render

No world generation, external assets, downloads, GPU configuration or engine exports.
Creates a NEW scene and refuses an existing output blend. All layout comes from the commission JSON.
"""
import bpy, json, math, sys, argparse, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/mickeys.json'
D=json.loads(DATA.read_text(encoding='utf-8'))
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',required=True)
parser.add_argument('--render',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=Path(args.output_dir).resolve()
if not out.is_relative_to(ROOT): raise RuntimeError('Outputs must remain inside this commission directory')
out.mkdir(parents=True,exist_ok=True)
if (out/'mickeys-blockout.blend').exists(): raise RuntimeError('Existing blockout preserved. Choose a new output subdirectory.')
scene=bpy.data.scenes.new('ATLAS01_Mickeys_Proposal')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('ATLAS01_Overcast')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.72,.76,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
base=bpy.data.collections.new('ATLAS01_Mickeys');scene.collection.children.link(base)
upper=bpy.data.collections.new('ATLAS01_Upper_Cutaway');scene.collection.children.link(upper)

def material(name,rgb):
    m=bpy.data.materials.new('A01_'+name);m.use_nodes=True
    n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*rgb,1);n.inputs['Roughness'].default_value=.76
    return m
materials={k:material(k,c) for k,c in {
    'brick':(.38,.20,.14),'plaster':(.68,.64,.51),'slate':(.12,.17,.18),
    'maroon':(.22,.045,.06),'wood':(.31,.17,.08),'glass_proxy':(.26,.46,.48),
    'floor':(.33,.27,.19),'yard':(.45,.43,.35),'metal':(.19,.24,.23),
    'cloth':(.26,.10,.10),'paper':(.78,.73,.56)}.items()}

def link_obj(obj,collection=base):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def box(name,u,v,h,su,sv,sh,mat='plaster',collection=base,bom='A01_PROPOSED',pivot='bounds_center'):
    assert min(su,sv,sh)>0,name
    bpy.ops.mesh.primitive_cube_add(size=1,location=(u,v,h))
    obj=link_obj(bpy.context.object,collection);obj.name='A01_'+name;obj.dimensions=(su,sv,sh)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(materials[mat]);obj['bom_id']=bom;obj['pivot_policy']=pivot
    obj['status']='spatial blockout; integration unverified'
    return obj

def rectbox(name,b,h,mat='wood',collection=base):
    u,v,w,d=b;return box(name,u+w/2,v+d/2,h/2,w,d,h,mat,collection)

def marker(name,p,kind):
    obj=bpy.data.objects.new('A01_BIND_'+name,None);base.objects.link(obj)
    obj.location=p;obj.empty_display_type='SPHERE';obj.empty_display_size=.12
    obj['proposed_binding']=kind;obj['runtime_binding']='NONE'
    return obj

def wall_with_openings(name,v,openings,h0=0,h1=3.4,collection=base):
    # Horizontal and vertical strips leave real holes, never a solid box behind a door.
    stops=sorted(set([0.,6.]+[float(o['start']) for o in openings]+[float(o['start']+o['width']) for o in openings]))
    for idx,(a,b) in enumerate(zip(stops,stops[1:])):
        mid=(a+b)/2;hit=next((o for o in openings if o['start']<mid<o['start']+o['width']),None)
        spans=[(h0,h1)] if not hit else [(h0,h0+hit.get('sill',0)),(h0+hit.get('sill',0)+hit['height'],h1)]
        for j,(lo,hi) in enumerate(spans):
            if hi-lo>.001:box(name+f'_{idx}_{j}',mid,v,(lo+hi)/2,b-a,.215,hi-lo,'brick',collection,'C1_terrace_carcass')
    for op in openings:
        u=op['start']+op['width']/2;sill=op.get('sill',0)
        if 'glass' in op['id'] or 'window' in op['id']:
            o=box(op['id'],u,v,h0+sill+op['height']/2,op['width'],.045,op['height'],'glass_proxy',collection,'C7_shop_glazing')
            o['note']='opaque proxy, not transparency or rendered visibility evidence'
        else:
            # Leaves are open by 90 degrees and pivot at hinge with local mesh offset.
            hinge_u=op['start']+.0225
            leaf=box(op['id']+'_leaf',hinge_u,v+op.get('swing_v',1)*op['width']/2,h0+op['height']/2,.045,op['width'],op['height'],'maroon',collection,'C8_door_shop' if 'public' in op['id'] else 'C9_door_side')
            hinge=marker(op['id']+'_hinge',(hinge_u,v,h0),'door hinge; lock/open state requested')
            bpy.context.view_layer.update()
            world=leaf.matrix_world.copy();leaf.parent=hinge;leaf.matrix_world=world
            marker(op['id']+'_threshold',(u,v,h0),'navigation threshold; not a live portal')

W=6;DEP=8;H=3.4;UH=2.8
box('ground_floor',3,4,-.10,6,8,.20,'floor',bom='A01_PUB_FLOOR')
box('south_partywall',.1075,4,1.7,.215,8,3.4,'brick',bom='C1_terrace_carcass')
box('north_partywall',5.8925,4,1.7,.215,8,3.4,'brick',bom='C1_terrace_carcass')
for side,v in [('front',.1075),('rear',7.8925)]:wall_with_openings(side,v,[o for o in D['openings'] if o['side']==side])
box('private_stair_partition',1.138,2.9075,1.7,.1,5.385,3.4)
for i in range(D['stairs']['risers']):
    rise=H/19;top=(i+1)*rise
    # Last riser meets landing; 18 goings span exactly 4.32 m.
    if i<18:box(f'stair_tread_{i:02}',.64,.3+(i+.5)*.24,top/2,.8,.24,top,'wood',bom='A01_PUB_STAIR')
box('stair_top_landing',.6775,5.11,H-.1,.925,.98,.2,'floor',upper,'A01_PUB_STAIR')
box('store_partition_top',1.1825,5.7,1.5,1.935,.1,3,'plaster')
box('store_partition_a',2.15,5.875,1.5,.1,.35,3,'plaster')
box('store_partition_b',2.15,7.3675,1.5,.1,.835,3,'plaster')
box('store_door_lintel',2.15,6.5,2.52,.1,.9,.96,'plaster')
for z in D['ground_zones']:
    if z['id'] in ['counter','backbar','snug']:
        rectbox(z['id'],z['box'],z['height'],'cloth' if z['id']=='snug' else 'wood')
for f in D['furniture']:
    h=f['height'];u,v,w,d=f['box']
    if f['id']=='till':box('till',u+w/2,v+d/2,1.20,w,d,.3,'metal',bom='A01_PUB_TILL')
    else:rectbox(f['id'],f['box'],h,'cloth' if 'bench' in f['id'] else 'wood')

# Upper floor with explicit void. Four rectangles surround the stair opening.
vu,vv,vw,vd=D['stairs']['floor_void']
for name,b in [('floor_south',[0,0,vu,8]),('floor_north',[vu+vw,0,6-vu-vw,8]),('floor_front',[vu,0,vw,vv]),('floor_rear',[vu,vv+vd,vw,8-vv-vd])]:
    u,v,w,d=b;box(name,u+w/2,v+d/2,3.3,w,d,.2,'floor',upper)
for side,v in [('upper_front',.1075),('upper_rear',7.8925)]:
    ops=[{'id':side+f'_window{i}','start':u,'width':.85,'sill':.9,'height':1.5} for i,u in enumerate([1.8,3.6])]
    wall_with_openings(side,v,ops,3.4,6.2,upper)
for u in [.1075,5.8925]:box('upper_party_'+str(u),u,4,4.8,.215,8,2.8,'brick',upper)
# Partition strips and doorway gaps, matching upper drawing.
for name,a,b in [('bed_a',.215,2.5),('bed_b',3.2,4.9),('living_b',5.6,5.8)]:
    box('upper_hall_'+name,2.3,(a+b)/2,4.8,.1,b-a,2.8,'plaster',upper)
box('bed_living_wall',4.04,3.475,4.8,3.48,.15,2.8,'plaster',upper)
for a,b in [(.215,1.5),(2.2,3.05),(3.75,4.65),(5.35,5.785)]:box('rear_room_front_'+str(a),(a+b)/2,5.95,4.8,b-a,.1,2.8,'plaster',upper)
for u in [2.375,4.175]:box('rear_room_divider_'+str(u),u,6.87,4.8,.15,1.835,2.8,'plaster',upper)
for room in D['upper_rooms']:
    u,v,w,d=room['box'];marker(room['id'],(u+w/2,v+d/2,3.4),'authored room; named for integration review')
box('bed',4.4,1.55,3.72,1.4,2,.64,'cloth',upper)
box('book_room_desk',1.25,7.35,3.775,1.3,.65,.75,'wood',upper)
box('kitchen_counter',3.25,7.45,3.86,1.4,.55,.92,'wood',upper)
box('bath_proxy',5.0,7.05,3.67,1.35,.65,.54,'plaster',upper)

ridge=6.2+4*math.tan(math.radians(35))
for side,v,ang in [('front',2,35),('rear',6,-35)]:
    o=box('roof_'+side,3,v,(6.2+ridge)/2,6.6,4.3/math.cos(math.radians(35)),.15,'slate',upper,'D1_roof_slate');o.rotation_euler.x=math.radians(ang)
for u in [0,6]:
    mesh=bpy.data.meshes.new('gable');mesh.from_pydata([(u,0,6.2),(u,8,6.2),(u,4,ridge)],[],[(0,1,2)]);mesh.update()
    ob=bpy.data.objects.new('A01_gable_'+str(u),mesh);upper.objects.link(ob);ob.data.materials.append(materials['brick'])
    box('chimney_'+str(u),u,4,ridge+.5,.9,.45,1,'brick',upper,'D2_chimney_stack')
box('fascia',3,-.06,3.125,6,.12,.55,'maroon',bom='C5_shopfront_assembly')
bpy.ops.object.text_add(location=(3,-.131,3.10),rotation=(math.pi/2,0,0))
label=link_obj(bpy.context.object);label.name='A01_Mickeys_lettering';label.data.body="MICKEY'S";label.data.align_x='CENTER';label.data.size=.33;label.data.materials.append(materials['paper'])
box('footway_context',3,-1,-.08,12,2,.16,'yard',bom='A0_ground_planes')
box('kerb_context',3,-2.0625,-.0625,12,.125,.125,'yard',bom='B1_kerbstone_run')
box('road_context',3,-5.125,-.20,22,6,.20,'metal',bom='A0_ground_planes')
box('yard',3,11,-.1,6,6,.2,'yard')
box('rear_lane',3,15.2,-.1,12,2.4,.2,'yard')
box('south_passage',-1.5,6,-.1,3,16,.2,'yard')
for name,u in [('yard_south',.075),('yard_north',5.925)]:box(name,u,11,.9,.15,6,1.8,'brick')
box('yard_back_a',2.3,13.925,.9,4.6,.15,1.8,'brick')
box('yard_back_b',5.9,13.925,.9,.2,.15,1.8,'brick')
marker('yard_gate',(4.6,14,0),'1.2 m hinge/gate state; proposed')
box('yard_gate_open_leaf',4.625,14.6,.9,.05,1.2,1.8,'wood',bom='A01_PUB_GATE')
# Annex: hollow 2.2 x 2.6 m envelope, 0.8m door toward the central yard.
box('wc_south',.1,9.3,1.275,.2,2.6,2.55,'brick')
for name,v in [('wc_west',8.1),('wc_east',10.5)]:box(name,1.1,v,1.275,2.2,.2,2.55,'brick')
for a,b in [(8,8.7),(9.5,10.6)]:box('wc_door_wall_'+str(a),2.1,(a+b)/2,1.275,.2,b-a,2.55,'brick')
box('wc_door_lintel',2.1,9.1,2.295,.2,.8,.51,'brick')
box('wc_roof',1.1,9.3,2.62,2.4,2.8,.14,'slate')
box('wc_pan_proxy',.7,9.8,.23,.4,.55,.46,'plaster')
box('wc_basin_proxy',.65,8.4,.8,.55,.35,.15,'plaster')
for name,p in D['information'].items():
    if isinstance(p,list):marker(name,(*p,1.6),'perception/acoustic design marker; untested')
for name,route in D['paths'].items():
    for i,p in enumerate(route):marker(name+f'_{i:02}',(*p,.1),'route intention; not navmesh')

def camera(spec):
    obj=bpy.data.objects.new('A01_CAM_'+spec['id'],bpy.data.cameras.new(spec['id']));scene.collection.objects.link(obj)
    obj.location=spec['position'];obj.rotation_euler=(Vector(spec['target'])-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.lens=spec['lens']
    return obj
cams={c['id']:camera(c) for c in D['cameras']}
ld=bpy.data.lights.new('A01_soft_sky','AREA');lo=bpy.data.objects.new('A01_soft_sky',ld);scene.collection.objects.link(lo);lo.location=(0,-2,15);ld.energy=2400;ld.shape='DISK';ld.size=18
ld2=bpy.data.lights.new('A01_bar_practical','AREA');lo2=bpy.data.objects.new('A01_bar_practical',ld2);scene.collection.objects.link(lo2);lo2.location=(3,4,3.15);ld2.energy=120;ld2.color=(1,.74,.43);ld2.size=3
scene.camera=cams['front']
bpy.ops.wm.save_as_mainfile(filepath=str(out/'mickeys-blockout.blend'))
receipt={'blender_version':bpy.app.version_string,'recipe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'scene':scene.name,'objects':len(scene.objects),'renders':[],'scope':'spatial blockout only; no engine export or runtime verification'}
if args.render:
    for c in D['cameras']:
        for obj in upper.objects:obj.hide_render=c.get('cutaway',False)
        scene.camera=cams[c['id']];scene.render.filepath=str(out/(c['id']+'.png'))
        bpy.ops.render.render(write_still=True);receipt['renders'].append(c['id']+'.png')
    for obj in upper.objects:obj.hide_render=False
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
