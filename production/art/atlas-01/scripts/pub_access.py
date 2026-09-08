"""Illustrate the retained anchor conflict and an unadopted geometric alternative."""
from draw import *
from pub_geometry import headroom
op=next(o for o in M['openings'] if o['id']=='private_entry');st=M['stairs'];wall=M['shell']['wall']
b='';s=100
for i,(title,start,recess) in enumerate([('A / retained design',st['start'][1],0),('B / unadopted recess',1.15,.95)]):
    ox=90+i*510;oy=360
    b+=text(ox,203,title,25,weight=700)
    b+=rect(ox,oy-200,300,200,'#d3cbb9')+text(ox+150,oy-130,'2 m footway',20,anchor='middle')
    b+=text(ox,203,title,25,weight=700)
    b+=rect(ox,oy,300,wall*s,INK)+rect(ox+op['start']*s,oy,op['width']*s,wall*s,BG)
    leaf_v=wall/2-op['width'] if i==0 else recess-op['width']
    b+=line(ox+op['start']*s,oy+(wall/2 if i==0 else recess)*s,ox+op['start']*s,oy+leaf_v*s,'#8a3e45',5)
    if i==1:b+=rect(ox+op['start']*s,oy+wall*s,op['width']*s,(recess-wall)*s,'#ece0c6',INK)
    for n in range(st['goings']):b+=rect(ox+st['start'][0]*s,oy+(start+n*st['going'])*s,st['width']*s,st['going']*s,'#b8a184',INK,.7)
    end=start+st['goings']*st['going'];land=st['landing_box'][3]
    b+=rect(ox+st['landing_box'][0]*s,oy+end*s,st['landing_box'][2]*s,land*s,'#afc0b4',INK)
    b+=line(ox,oy+5.7*s,ox+300,oy+5.7*s,'#973f4c',3,'6 4')+text(ox+115,oy+5.7*s-10,'Store begins',16,'#973f4c')
    rows=([f'Inner wall to first tread: {start-wall:.3f} m',f'Leaf extends {op["width"]-wall/2:.3f} m', 'beyond the facade plane.','No pose or navigation test.'] if i==0 else ['Same facade aperture; leaf recessed.','Run ends at 5.47 m; landing at 6.45 m.','Overlaps current store by 0.75 m.','Requires a deliberate redesign.'])
    for j,row in enumerate(rows):b+=text(ox,1065+j*28,row,18,MUTED)
b+=text(60,1210,'A keeps the current recipe. B is a comparison, not an approved layout or an automatic edit.',18,weight=700)
b+=text(60,1244,'A different stair arrangement or shared internal access remains a design decision.',18,MUTED)
b+=text(60,1278,'Dimensions are authored calculations. No building-code or real-world safety finding is claimed.',17,MUTED)
save('mickeys-access',1130,1380,b,"Mickey's / the access conflict",'SOURCE APERTURE RETAINED / ALTERNATIVE NOT ADOPTED')
