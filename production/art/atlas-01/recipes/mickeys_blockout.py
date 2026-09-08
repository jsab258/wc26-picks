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
sys.path.insert(0,str(ROOT/'scripts'))
from pub_geometry import geometry, resolved, digest
D=resolved(json.loads(DATA.read_text(encoding='utf-8')))
G=geometry(D)
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir','--out',dest='output_dir',required=True)
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

# Both plans and this adapter consume the same explicit geometry commands.
for b in G['boxes']:
    u,v,w,d=b['box']
    obj=box(b['id'],u+w/2,v+d/2,b['base']+b['height']/2,w,d,b['height'],b['material'],upper if b['floor']=='upper' else base,b['bom'])
    obj.rotation_euler.x=math.radians(b['rotation_x'])
for tri in G['triangles']:
    mesh=bpy.data.meshes.new(tri['id']);mesh.from_pydata(tri['vertices'],[],[(0,1,2)]);mesh.update()
    obj=bpy.data.objects.new('A01_'+tri['id'],mesh);upper.objects.link(obj);obj.data.materials.append(materials[tri['material']])
for door in G['doors']:
    hinge=marker(door['id']+'_hinge',door['hinge'],'door hinge; proposed state only')
    leaf=bpy.data.objects.get('A01_'+door['id']+'_leaf') or bpy.data.objects.get('A01_'+door['id']+'_open_leaf')
    if leaf:
        bpy.context.view_layer.update();world=leaf.matrix_world.copy();leaf.parent=hinge;leaf.matrix_world=world
    marker(door['id']+'_threshold',door['threshold'],'navigation threshold; not a live portal')
for room in D['upper_rooms']:
    u,v,w,d=room['box'];marker(room['id'],(u+w/2,v+d/2,D['shell']['ground_floor_height']),'authored room')
label_data=D['fascia_text']
bpy.ops.object.text_add(location=label_data['position'],rotation=(math.pi/2,0,0))
label=link_obj(bpy.context.object);label.name='A01_Mickeys_lettering';label.data.body=label_data['text'];label.data.align_x='CENTER';label.data.size=label_data['size'];label.data.materials.append(materials['paper'])
for name,p in D['information'].items():
    if isinstance(p,list):marker(name,(*p,D['information']['eye_height']),'perception/acoustic design marker; untested')
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
receipt={'blender_version':bpy.app.version_string,'recipe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'geometry_sha256':digest(D),'geometry_compiler_sha256':hashlib.sha256((ROOT/'scripts/pub_geometry.py').read_bytes()).hexdigest(),'scene':scene.name,'objects':len(scene.objects),'renders':[],'scope':'spatial blockout only; no engine export or runtime verification'}
if args.render:
    for c in D['cameras']:
        for obj in upper.objects:obj.hide_render=c.get('cutaway',False)
        scene.camera=cams[c['id']];scene.render.filepath=str(out/(c['id']+'.png'))
        bpy.ops.render.render(write_still=True);receipt['renders'].append(c['id']+'.png')
    for obj in upper.objects:obj.hide_render=False
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
