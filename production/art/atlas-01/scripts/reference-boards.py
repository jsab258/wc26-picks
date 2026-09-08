"""Compose research-only source images and original analytic diagrams as SVG boards."""
from pathlib import Path
import base64, sys
sys.path.insert(0,str(Path(__file__).parent))
from draw import text,line,rect,path,save,INK,MUTED,BG
ROOT=Path(__file__).resolve().parents[1]
def photo(name,x,y,w,h,view=None):
    p=ROOT/'references'/name
    mime='image/jpeg' if p.suffix=='.jpg' else 'image/png'
    uri='data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
    if view:
        vx,vy,vw,vh,iw,ih=view
        return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="xMidYMid meet"><image width="{iw}" height="{ih}" href="{uri}"/></svg>'
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri}" preserveAspectRatio="xMidYMid meet"/>'
def notes(x,y,rows,size=21):return ''.join(text(x,y+i*30,s,size,MUTED) for i,s in enumerate(rows))

b=photo('hull-west-dock-1981.jpg',40,185,530,380)
b+=text(600,219,'1981 / working frontage',26,weight=700)
b+=notes(600,265,['Recessed door creates a pause.','Angled glazing frames a partial view.','Curtains keep domestic life present.','Tiled threshold records daily wear.','','Not a modern cafe frontage.'])
b+=text(40,605,'Peter Marshall / West Dock Cafe, Hull / 1981',20,weight=700)
b+=photo('hull-map.png',40,650,530,370,(100,120,550,400,778,1100))
b+=text(600,690,'1842 map / deep structure',26,weight=700)
b+=notes(600,735,['Water once enclosed the Old Town.','Small riverside passages meet','larger commercial routes.','','Map date does not establish','the use of a building in 1990.'])
b+=text(40,1060,'DERIVED RULE / a front conceals a working depth',25,weight=700)
# Original analytic diagram, not a traced town plan.
b+=rect(60,1110,990,65,'#7c8b8a')+text(555,1151,'PUBLIC STREET',22,'white','middle',700)
for i,(label,depth) in enumerate([('shop',200),('pub',245),('store',175),('house',220)]):
    x=80+i*220;b+=rect(x,1190,175,depth,'#c4ac8a',INK,2)+text(x+87,1225,label,22,anchor='middle')
    b+=rect(x+12,1250,151,depth-75,'#dfd2b7',INK)+text(x+87,1290,'work / yard',18,anchor='middle')
b+=path([[295,1190],[295,1455],[1050,1455]],'none','#21676b',7)
b+=text(610,1500,'Narrow plot fronts; deliberately connected rear access.',21,MUTED,'middle')
b+=notes(40,1565,['Period caution: Castle Street was divided by 1970s road works.','Marina regeneration began in the early 1980s; do not erase it from period research.'],20)
b+=text(40,1660,'Sources and rights: TOWN-FORM-BIBLE.md / research use only, not game assets.',18,MUTED)
save('reference-hull',1120,1760,b,'Hull / the inhabited threshold','REFERENCE PHOTOGRAPH + HISTORIC MAP + ORIGINAL ANALYSIS')

b=photo('kasbah-character-09.png',40,185,1040,290,(0,0,705,190,708,1000))
b+=text(40,515,'2017 / surviving industrial fabric, not a 1990 condition claim',24,weight=700)
b+=notes(40,560,['Roof heights change by plot; sheet repairs sit beside brick and slate.','Altered openings explain changes of use. Keep repair histories specific.'],21)
b+=photo('kasbah-map.png',40,670,520,580,(30,110,710,820,778,1100))
b+=text(600,705,'2017 map / transport first',26,weight=700)
b+=notes(600,752,['Docks and rail shaped residual plots.','Narrow frontage can hide deep sheds.','Haulage widened selected routes.','','The modern vacant fabric cannot','stand for the whole working port','during 1988-1992.','','Map shown for analysis only.','No geometry is traced into Meridian.'])
b+=text(40,1310,'DERIVED RULE / the yard is a destination',25,weight=700)
b+=path([[65,1540],[450,1365],[1020,1390]],'none','#5c6561',10,False,'20 8')
b+=rect(110,1360,210,60,'#aa8069',INK,2)+text(215,1400,'WORKSHOP',20,anchor='middle')
b+=rect(530,1440,300,140,'#d1bb92',INK,2)+text(680,1520,'NAMED SERVICE YARD',20,anchor='middle')
b+=rect(880,1440,190,140,'#8a9394',INK,2)+text(975,1520,'LOADING',20,'white','middle')
b+=path([[460,1610],[460,1535],[530,1535]],'none','#21676b',6)
b+=text(40,1655,'One visible gate, a known work route, an oblique rail trace, altered shed fronts.',20,MUTED)
b+=text(40,1705,'NELC / ENGIE / OS Crown map credits retained in source. Research-only images.',18,MUTED)
save('reference-kasbah',1120,1810,b,'Kasbah / work behind the frontage','MODERN HERITAGE EVIDENCE + ORIGINAL ANALYSIS')
print('Wrote two annotated reference boards.')
