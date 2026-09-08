"""Read actual GLB triangles; write orthographic source-geometry inspections.
No Blender, lighting, material or engine rendering. Inputs must be supplied explicitly.
Usage: python inspect_meshes.py /directory/containing/reviewed/glb/files
"""
import json,struct,hashlib,sys,math
from pathlib import Path
from draw import rect,text,path,save,OUT
ROOT=Path(__file__).resolve().parents[1]
NAMES=['drainage_grate_01','drain_cover_01','outdoor_bin','pavement_sign','framed_poster','lamp_post_01','pallet','wood_barrel']
def load(p):
 raw=p.read_bytes(); assert raw[:4]==b'glTF';off=12;chunks={}
 while off<len(raw):
  n,t=struct.unpack_from('<II',raw,off);chunks[t]=raw[off+8:off+8+n];off+=8+n
 d=json.loads(chunks[0x4e4f534a]);buf=chunks[0x004e4942]
 def acc(idx):
  a=d['accessors'][idx];v=d['bufferViews'][a['bufferView']];fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=struct.calcsize(fmt)*n;start=v.get('byteOffset',0)+a.get('byteOffset',0)
  return [struct.unpack_from('<'+fmt*n,buf,start+i*v.get('byteStride',size)) for i in range(a['count'])]
 verts=[];faces=[]
 # Apply complete ancestor TRS chains; matrices fail rather than misreport dimensions.
 def rotate(v,q):
  x,y,z,w=q;vx,vy,vz=v;tx=2*(y*vz-z*vy);ty=2*(z*vx-x*vz);tz=2*(x*vy-y*vx)
  return [vx+w*tx+y*tz-z*ty,vy+w*ty+z*tx-x*tz,vz+w*tz+x*ty-y*tx]
 nodes=d.get('nodes',[]);parents={child:i for i,node in enumerate(nodes) for child in node.get('children',[])}
 def world(v,idx):
  seen=set()
  while idx is not None:
   assert idx not in seen;seen.add(idx);n=nodes[idx];assert 'matrix' not in n,(p,'matrix')
   v=rotate([v[k]*n.get('scale',[1,1,1])[k] for k in range(3)],n.get('rotation',[0,0,0,1]));v=[v[k]+n.get('translation',[0,0,0])[k] for k in range(3)];idx=parents.get(idx)
  return v
 for idx,node in enumerate(nodes):
  if 'mesh' not in node:continue
  assert 'matrix' not in node,(p,'matrix')
  scale=node.get('scale',[1,1,1]);translate=node.get('translation',[0,0,0])
  for prim in d['meshes'][node['mesh']]['primitives']:
   assert prim.get('mode',4)==4
   vv=acc(prim['attributes']['POSITION']);ii=[x[0] for x in acc(prim['indices'])] if 'indices' in prim else list(range(len(vv)))
   shift=len(verts)
   for v in vv:
    verts.append(world(v,idx))
   faces.extend([[shift+x for x in ii[i:i+3]] for i in range(0,len(ii),3)])
 lo=[min(v[k] for v in verts) for k in range(3)];hi=[max(v[k] for v in verts) for k in range(3)]
 return verts,faces,dict(sha256=hashlib.sha256(raw).hexdigest(),bounds_min=lo,bounds_max=hi,dimensions_xyz=[hi[k]-lo[k] for k in range(3)],vertices=len(verts),triangles=len(faces),materials=len(d.get('materials',[])),images=len(d.get('images',[])))
def main(folder):
 records=[]
 for name in NAMES:
  vv,ff,r=load(folder/(name+'.glb'));r['mesh_id']=name;records.append(r);b=''
  for j,(a,c,label) in enumerate([(0,1,'FRONT / XY'),(2,1,'SIDE / ZY'),(0,2,'TOP / XZ')]):
   ox=35+j*310;oy=225;w=270;h=330;lo=r['bounds_min'];hi=r['bounds_max'];s=min(w/max(.001,hi[a]-lo[a]),h/max(.001,hi[c]-lo[c]));cx=(hi[a]+lo[a])/2;cy=(hi[c]+lo[c])/2
   for i,f in enumerate(ff):
    pts=[(ox+w/2+(vv[k][a]-cx)*s,oy+h/2-(vv[k][c]-cy)*s) for k in f]
    b+=path(pts,['#a2b0ad','#bbc6c1','#d1d5c9'][i%3],'#647872',.3,True)
   b+=text(ox,195,label,18)+text(ox,595,f'{hi[a]-lo[a]:.3f} × {hi[c]-lo[c]:.3f} m',21)
  b+=text(38,650,f'{r["vertices"]} vertices / {r["triangles"]} triangles / {r["materials"]} slots / {r["images"]} images',19)
  save('mesh-'+name,980,760,b,name,'ACTUAL SOURCE GEOMETRY / ORTHOGRAPHIC PROJECTION / NO MATERIAL OR ENGINE CLAIM')
 (ROOT/'data/mesh-inspections.json').write_text(json.dumps(records,indent=2)+'\n')
 print('Inspected',len(records),'actual GLBs')
if __name__=='__main__':main(Path(sys.argv[1]))
