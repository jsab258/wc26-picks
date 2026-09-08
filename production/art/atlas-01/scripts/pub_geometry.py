"""Geometry arithmetic shared by the SVG drawing and Blender adapter.

This compiles explicit rectangles, wall edges and openings. It never chooses a
room, furnishing or route. Metres in commission [u,v,h]. No Blender dependency.
"""
import copy, hashlib, json, math

def resolved(data):
    d=copy.deepcopy(data);s=d['stairs']
    for z in d['ground_zones']:
        if z['id']=='stair':z['box']=[*s['start'],s['width'],s['goings']*s['going']]
    return d

def geometry(data):
    d=resolved(data);s=d['shell'];st=d['stairs'];w=s['width'];dep=s['depth'];t=s['wall'];h=s['ground_floor_height'];uh=s['upper_height'];ft=s['floor_thickness']
    boxes=[];triangles=[];doors=[]
    def box(id,b,z,height,mat='plaster',floor='ground',bom='A01_PROPOSED',rotation_x=0):
        u,v,ww,dd=b
        if min(ww,dd,height)<=0:raise ValueError('Nonpositive authored geometry: '+id)
        boxes.append(dict(id=id,box=[u,v,ww,dd],base=z,height=height,material=mat,floor=floor,bom=bom,rotation_x=rotation_x))
    def wall(id,segment,thick,z,height,ops,mat='plaster',floor='ground'):
        u,v,uu,vv=segment;along_u=vv==v
        if not (along_u or uu==u):raise ValueError('Only explicitly orthogonal partitions are supported')
        length=uu-u if along_u else vv-v
        for o in ops:
            if o['offset']<0 or o['offset']+o['width']>length+1e-8:raise ValueError('Opening outside '+id)
        cuts=sorted({0,length,*[q for o in ops for q in [o['offset'],o['offset']+o['width']]]})
        for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
            hit=next((o for o in ops if o['offset']<(a+b)/2<o['offset']+o['width']),None)
            spans=[(0,height)] if hit is None else [(0,hit.get('sill',0)),(hit.get('sill',0)+hit['height'],height)]
            for j,(lo,hi) in enumerate(spans):
                if hi-lo>1e-8:box(f'{id}_{i}_{j}',[u+a,v-thick/2,b-a,thick] if along_u else [u-thick/2,v+a,thick,b-a],z+lo,hi-lo,mat,floor,'C1_terrace_carcass' if mat=='brick' else 'A01_PUB_PARTITIONS')
    def frontage(prefix,ops,z,height,floor):
        for side,v in [('front',t/2),('rear',dep-t/2)]:
            selected=[o for o in ops if o['side']==side]
            wall(prefix+side,[0,v,w,v],t,z,height,[dict(o,offset=o['start']) for o in selected],'brick',floor)
            for o in selected:
                if o['kind']=='glass':box(o['id'],[o['start'],v-.0225,o['width'],.045],z+o.get('sill',0),o['height'],'glass_proxy',floor,'C7_shop_glazing')
                else:
                    swing=o.get('swing_v',1);a=v if swing==1 else v-o['width']
                    box(o['id']+'_leaf',[o['start'],a,.045,o['width']],z,o['height'],'maroon',floor,'C8_door_shop' if 'public' in o['id'] else 'C9_door_side')
                    doors.append(dict(id=o['id'],hinge=[o['start']+.0225,v,z],threshold=[o['start']+o['width']/2,v,z]))
    box('ground_floor',[0,0,w,dep],-ft,ft,'floor',bom='A01_PUB_FLOOR')
    for floor,z,height in [('ground',0,h),('upper',h,uh)]:
        box(floor+'_south_partywall',[0,0,t,dep],z,height,'brick',floor,'C1_terrace_carcass')
        box(floor+'_north_partywall',[w-t,0,t,dep],z,height,'brick',floor,'C1_terrace_carcass')
    frontage('',d['openings'],0,h,'ground');frontage('upper_',d['upper_openings'],h,uh,'upper')
    p=st['partition'];box('private_stair_partition',p['box'],0,p['height'])
    rise=h/st['risers'];u,v=st['start']
    for i in range(st['goings']):box(f'stair_tread_{i:02}',[u,v+i*st['going'],st['width'],st['going']],0,(i+1)*rise,'wood',bom='A01_PUB_STAIR')
    box('stair_top_landing',st['landing_box'],h-ft,ft,'floor','upper','A01_PUB_STAIR')
    vu,vv,vw,vd=st['floor_void']
    for id,b in [('floor_south',[0,0,vu,dep]),('floor_north',[vu+vw,0,w-vu-vw,dep]),('floor_front',[vu,0,vw,vv]),('floor_rear',[vu,vv+vd,vw,dep-vv-vd])]:box(id,b,h-ft,ft,'floor','upper')
    rooms={r['id']:r for r in d['ground_zones']+d['upper_rooms']}
    for p in d['partitions']:
        if 'segment' in p:segment=p['segment']
        else:
            u,v,ww,dd=rooms[p['room']]['box'];a=p['thickness']/2 if p.get('outside') else 0
            segment={'front':[u,v, u+ww,v],'back':[u,v+dd+a,u+ww,v+dd+a],'right':[u+ww+a,v,u+ww+a,v+dd],'left':[u,v,u,v+dd]}[p['edge']]
        height=s[p['height']] if isinstance(p['height'],str) else p['height']
        wall(p['id'],segment,p['thickness'],h if p['floor']=='upper' else 0,height,p['openings'],floor=p['floor'])
    for f in [z for z in d['ground_zones'] if z.get('solid')]+d['furniture']:
        box(f['id'],f['box'],f.get('base_h',0),f['height'],f['material'])
    for f in d['upper_furniture']:
        ru,rv,_,_=rooms[f['room']]['box'];u,v,ww,dd=f['box']
        box(f['id'],[ru+u,rv+v,ww,dd],h+f['base_h'],f['height'],f['material'],'upper')
    e=h+uh;pitch=s['roof_pitch_deg'];ridge=e+dep/2*math.tan(math.radians(pitch));over=s['eaves_overhang']
    for id,v,ang in [('front',dep/4,pitch),('rear',dep*3/4,-pitch)]:
        length=(dep/2+over)/math.cos(math.radians(pitch))
        box('roof_'+id,[-over,v-length/2,w+2*over,length],(e+ridge)/2-s['roof_thickness']/2,s['roof_thickness'],'slate','upper','D1_roof_slate',ang)
    for u in [0,w]:
        triangles.append(dict(id='gable_'+str(u),vertices=[[u,0,e],[u,dep,e],[u,dep/2,ridge]],material='brick',floor='upper'))
        ch=d['chimney'];box('chimney_'+str(u),[u-ch['width']/2,dep/2-ch['depth']/2,ch['width'],ch['depth']],ridge,ch['height'],'brick','upper','D2_chimney_stack')
    for f in d['detail_boxes']:
        u,v,z=f['center'];ww,dd,hh=f['size'];box(f['id'],[u-ww/2,v-dd/2,ww,dd],z-hh/2,hh,f['material'],f['floor'],f['bom'])
    y=d['yard'];yw=y['width'];yd=y['depth'];ys=y['start_v'];yt=y['wall_thickness'];yh=y['wall_height'];back=ys+yd;gate=y['gate_start'];gw=y['gate_width']
    box('yard',[0,ys,yw,yd],-ft,ft,'yard');box('rear_lane',[-3,back,yw+6,y['rear_lane_width']],-ft,ft,'yard')
    for id,u in [('south',0),('north',yw-yt)]:box('yard_'+id,[u,ys,yt,yd],0,yh,'brick')
    wall('yard_back',[0,back-yt/2,yw,back-yt/2],yt,0,yh,[dict(offset=gate,width=gw,height=yh)],'brick')
    box('yard_gate_open_leaf',[gate,back,.05,gw],0,yh,'wood',bom='A01_PUB_GATE')
    doors.append(dict(id='yard_gate',hinge=[gate+.025,back,0],threshold=[gate+gw/2,back,0]))
    u,v,ww,dd=y['wc_annex'];wt=y['wc_wall'];wh=y['wc_height']
    box('wc_south',[u,v,wt,dd],0,wh,'brick')
    for id,q in [('west',v),('east',v+dd-wt)]:box('wc_'+id,[u,q,ww,wt],0,wh,'brick')
    wall('wc_door_wall',[u+ww-wt/2,v,u+ww-wt/2,v+dd],wt,0,wh,[dict(offset=y['wc_door_offset'],width=y['wc_door_width'],height=y['wc_door_height'])],'brick')
    box('wc_roof',[u-.1,v-.1,ww+.2,dd+.2],wh,.14,'slate')
    return dict(boxes=boxes,triangles=triangles,doors=doors)

def plan_boxes(data,upper=False):
    """Actual adapter commands projected at a floor's cut plane, with furniture."""
    g=geometry(data);h=data['shell']['ground_floor_height'] if upper else 0
    floor='upper' if upper else 'ground'
    return [b for b in g['boxes'] if b['floor']==floor and b['rotation_x']==0 and b['base']<h+1.2 and b['base']+b['height']>h and b['id'] not in ['wc_roof']]

def digest(data):return hashlib.sha256(json.dumps(geometry(data),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def headroom(data):
    st=data['stairs'];s=data['shell'];start=st['start'][1];void_v=st['floor_void'][1]
    # Count treads with any footprint under the front slab; the worst is highest.
    under=[i+1 for i in range(st['goings']) if start+i*st['going']<void_v-1e-9]
    return s['ground_floor_height']-s['floor_thickness']-max(under,default=0)*s['ground_floor_height']/st['risers']
