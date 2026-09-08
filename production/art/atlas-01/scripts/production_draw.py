"""Original asset-specific target details and exact-text vector proofs. Not 3D renders."""
from draw import *
B=json.loads((ROOT/'data/first-batch.json').read_text(encoding='utf-8'))
def target(a):
 n=a['mesh_id'];w,h,d=a['dimensions_m'];scale=min(820/w,340/h);x=80;y=600;ww=w*scale;hh=h*scale
 b=text(50,200,'Front target / exact envelope below',23,weight=700)
 b+=rect(x,y-hh,ww,hh,'#a88a67',INK,2)
 if 'fascia' in n:
  b+=rect(x+3,y-hh+3,ww-6,hh-6,'#582b36','#d9bd79',2)
  if 'plate' in n:b+=text(x+ww/2,y-hh/2+12,"MICKEY’S",min(50,hh*.55),'#e8cc87','middle',700)
 if 'counter' in n:
  b=text(50,200,'Long side / washing zone at rear end',23,weight=700)
  b+=rect(80,315,800,200,'#8f6e50',INK)+rect(80,305,800,18,'#705042',INK)
  for j in range(4):b+=rect(93+j*153,338,137,158,'#664732',INK)
  b+=rect(740,324,125,88,'#babdaf',INK)+text(792,446,'SINK',18,anchor='middle')+text(80,565,'4.2m run / 0.6m depth / 0.8m washing zone',22)
 if 'till' in n:
  b+=rect(x,y-hh,ww,hh,'#ccc7b5',INK)+rect(x+ww*.08,y-hh*.92,ww*.7,hh*.22,'#324348',INK)+text(x+ww*.43,y-hh*.76,'0.00',28,'#c8d6b9','middle')
  for i in range(12):b+=rect(x+30+(i%4)*ww*.18,y-hh*.55+(i//4)*30,ww*.12,22,'#445052',INK)
  b+=line(x,y-35,x+ww,y-35,INK,3)+rect(x+ww*.45,y-22,ww*.1,5,INK)
 if 'beer_engine' in n:
  b= text(50,200,'Hand-pull target / separate handle and spout',23,weight=700)+rect(375,500,150,55,'#665041',INK)+rect(410,375,45,130,'#bdbbaa',INK)+path([[435,380],[435,300],[465,260]],'none',INK,14)+path([[455,415],[510,415],[520,443]],'none','#b2a16f',9)+circle(464,253,19,'#582b36',INK)
 if 'table' in n:
  b+=rect(x,y-hh,ww,hh,BG)+rect(x,y-hh,ww,18,'#775139',INK)+rect(x+12,y-hh+18,22,hh-18,'#684631',INK)+rect(x+ww-34,y-hh+18,22,hh-18,'#684631',INK)+line(x+25,y-70,x+ww-25,y-70,INK,8)
 if 'screen' in n:
  b+=rect(x+12,y-hh+15,ww-24,hh-32,'#8e6e51',INK)
  for j in range(4):b+=line(x+(j+1)*ww/5,y-hh+15,x+(j+1)*ww/5,y-17,INK,4)
 if 'net' in n:
  b+=rect(x,y-hh,ww,hh,'#dfddd0',INK)
  for j in range(36):b+=path([[x+j*ww/36,y-hh],[x+j*ww/36+6,y-hh/2],[x+j*ww/36,y]],'none','#9bada7',2)
  b+=text(70,630,'Open weave requires a separate alpha/perception decision.',19)
 if 'metal_bin' in n:
  b+=rect(x,y-hh,ww,hh,'#999f97',INK)
  for j in range(9):b+=line(x+(j+1)*ww/10,y-hh+25,x+(j+1)*ww/10,y-18,'#ced0bd',3)
  b+=rect(x-8,y-hh-12,ww+16,24,'#aab0a4',INK)+rect(x+ww*.4,y-hh-30,ww*.2,18,'#9da397',INK)
 if 'notice_paper' in n:
  b+=rect(x,y-hh,ww,hh,'#eee5cd',INK)+text(x+ww/2,y-hh+48,'MICKEY’S',32,anchor='middle',weight=700)+text(x+ww/2,y-hh+90,'OPENING HOURS',20,anchor='middle')
  for j,t in enumerate(['MON–SAT','11.30–2.30','5.30–11.00','SUNDAY','12–3 / 7–10.30']):b+=text(x+ww/2,y-hh+140+j*32,t,21,anchor='middle')
 b+=text(50,715,f'{w:g}m width × {h:g}m height × {d:g}m depth',25,weight=700)+text(50,758,f'Quantity: {a["quantity"]} / {a["id"]}',20)
 b+=text(50,805,'Construction, variants, placements and bindings: data/first-batch.json',18)
 save('target-'+n,980,910,b,a['name'],'ORIGINAL DESIGN TARGET / NOT AN EXISTING-ASSET INSPECTION OR RENDER')
def proof(name,w,h,body):
 dest=ROOT/'artwork';dest.mkdir(exist_ok=True)
 (dest/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font-family:Georgia,serif}}</style>'+body+'</svg>',encoding='utf-8')
 # Preview is copied vector source, not a raster texture claim.
 (OUT/(name+'.svg')).write_text((dest/(name+'.svg')).read_text(encoding='utf-8'),encoding='utf-8')
if __name__=='__main__':
 for a in B['items']:
  if a['acquisition']!='reuse':target(a)
 proof('fascia_mickeys-layout-proof',6000,550,rect(0,0,6000,550,'#582b36')+rect(55,45,5890,460,'none','#d9bd79',12)+text(3000,390,"MICKEY’S",340,'#e8cc87','middle',700))
 proof('mickeys-hours-proof',420,594,rect(0,0,420,594,'#eee5cd')+text(210,78,"MICKEY’S",47,anchor='middle',weight=700)+text(210,140,'OPENING HOURS',30,anchor='middle')+''.join(text(210,208+i*43,t,25,anchor='middle') for i,t in enumerate(['MONDAY–SATURDAY','11.30–2.30','5.30–11.00','SUNDAY','12–3 / 7–10.30','PLEASE LEAVE QUIETLY'])))
 proof('mickeys-returns-proof',600,300,rect(0,0,600,300,'#e2d4b7')+text(300,78,'DELIVERIES',46,anchor='middle',weight=700)+text(300,151,'PLEASE KNOCK',38,anchor='middle')+text(300,224,'EMPTIES TO REAR',38,anchor='middle'))
 proof('mickeys-pump-clip-proof',300,380,rect(0,0,300,380,'#582b36')+rect(13,13,274,354,'none','#d9bd79',5)+text(150,95,'CLAYBANK',36,'#eee0b0','middle',700)+text(150,185,'BITTER',43,'#eee0b0','middle',700)+text(150,290,'MERIDIAN',26,'#eee0b0','middle'))
 # Bind individual targets to the active audit without changing original IDs.
 a=json.loads((ROOT/'data/assets.json').read_text());idx={x['id']:x for x in B['items']}
 for row in a['items']:
  if row['id'] in idx and idx[row['id']]['acquisition']!='reuse':
   row['thumbnail']=idx[row['id']]['picture'];row['thumbnail_kind']=idx[row['id']]['picture_kind']
 (ROOT/'data/assets.json').write_text(json.dumps(a,indent=2)+'\n')
 print('10 asset details and 4 exact-text proofs')
