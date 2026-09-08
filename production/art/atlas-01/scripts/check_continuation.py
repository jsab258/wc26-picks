"""Focused continuation contracts; no Blender, Unreal, model download or network."""
from pathlib import Path
import json,math,hashlib,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((R/p).read_text(encoding='utf-8'))
A=read('data/assets.json');B=read('data/first-batch.json');M=read('data/mickeys.json');O=read('data/pub-operations.json');checks=[]
def check(n,c):assert c,n;checks.append(n)
ids={x['id'] for x in A['items']}
check('All original identities retained and unique',len(ids)==len(A['items'])==98 and sum(x['id_kind']=='existing BOM' for x in A['items'])==77)
check('Availability, suitability and integration independent',all(all(x.get(k) for k in ['availability','suitability','integration_status']) and 'status' not in x for x in A['items']))
check('Batch IDs and dependencies resolve',len(B['items'])==12 and all(x['id'] in ids and all(y in ids for y in x['dependencies']) for x in B['items']))
check('Named placement counts explicit',all(x['quantity']==len(x['placements']) for x in B['items']) and sum(x['quantity'] for x in B['items'])==16)
check('Each batch package has an individual picture',all((R/x['picture']).exists() for x in B['items']) and len({x['picture'] for x in B['items']})==12)
check('No unsupported material names in static batch',all(x['surface'] in ['wood','metal','card'] for x in B['items']))
check('No accidental duplicate new global BOM IDs',all(x['id'] in ids for x in B['items']))
check('Named frontages retain twelve existing source bay IDs',len(O['neighbours'])==len({x[0] for x in O['neighbours']})==12)
check('Operational till envelope agrees with repaired geometry',O['bar_work']['till_box']==next(f['box'] for f in M['furniture'] if f['id']=='till'))
st=O['beer_store'];check('Beer-store allocation stays inside actual room',all(st['room_box'][0]<=st[k][0] and st['room_box'][1]<=st[k][1] and st[k][0]+st[k][2]<=sum(st['room_box'][::2]) and st[k][1]+st[k][3]<=sum(st['room_box'][1::2]) for k in ['stillage_box','reserve_box']))
check('Beer-store aisle derived from allocation',math.isclose(st['clear_centre_aisle_m'],st['reserve_box'][0]-st['stillage_box'][0]-st['stillage_box'][2]))
g=read('render-request.json');check('Published recipe inputs unchanged by research continuation',all(hashlib.sha256((R/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h for p,h in g['input_sha256_git_blob_bytes'].items()))
pilot=read('data/pilot-image-inputs.json');check('Single explicitly seeded image input, no fascia reseed',len(pilot['items'])==1 and pilot['items'][0]['id']=='a01_maroon_timber_sample' and pilot['items'][0]['seed']==8101001)
check('Generated text proofs contain no Windows decoding damage',all(not any(t in p.read_text(encoding='utf-8') for t in ['â€','Ã','�']) for p in (R/'previews').glob('*.svg')))
for p in (R/'artwork').glob('*.svg'):ET.parse(p)
check('Four SVG artwork proofs parse',len(list((R/'artwork').glob('*.svg')))==4)
(R/'verification-continuation.json').write_text(json.dumps({'kind':'source/specification checks, not PC execution','count':len(checks),'passed':checks},indent=2)+'\n',encoding='utf-8')
print(len(checks),'continuation checks passed')
