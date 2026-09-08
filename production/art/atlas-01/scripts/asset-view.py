"""Readable asset audit from authored judgments. No asset-status inference from file existence."""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/assets.json').read_text())
e=lambda s:html.escape(str(s))
cards=[]
for a in d['items']:
    cards.append(f'''<article data-search="{e(a['id']+' '+a['name']+' '+a['status'])}" data-priority="{a['priority']}">
    <img src="{e(a['thumbnail'])}" alt="{e(a['thumbnail_kind'])}" loading="lazy"><div>
    <small>P{a['priority']} / {e(a['id_kind'])} / {e(a['kind'])}</small><h2>{e(a['id'])}</h2>
    <h3>{e(a['name'])}</h3><strong class="{a['status']}">{e(a['status']).upper()}</strong>
    <p>{e(a['basis'])}</p><p><b>Picture:</b> {e(a['thumbnail_kind'])}</p>
    <p><b>Placements:</b> {e(a['placements'])}</p><p><b>Variant:</b> {e(a['variant_intention'])}</p>
    <p><b>State:</b> {e(a['stateful_requirement'])}</p><p><b>Engine:</b> {e(a['engine_integration'])}</p>
    <small>Source primitive entries: {e(a.get('source_primitive_entries','n/a'))}. Related BOM: {e(', '.join(a.get('related_existing_bom_ids',[])) or a['id'])}</small></div></article>''')
doc='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LEDGER atlas 01 asset audit</title>
<style>body{margin:auto;max-width:1100px;padding:24px;background:#f5f0e5;color:#253a3d;font:17px/1.5 system-ui}h1{font-size:38px}h2{font-size:20px;overflow-wrap:anywhere}h3{font-size:18px}article{display:grid;grid-template-columns:220px 1fr;gap:24px;border-top:1px solid #abb5aa;padding:24px 0}img{width:100%;max-height:340px;object-fit:contain;object-position:top}small{color:#546869}strong{padding:4px 10px}.usable{background:#bad1b1}.revise{background:#ead19b}.missing{background:#dfb7ae}input,select{font:inherit;padding:10px;margin:5px}nav{position:sticky;top:0;background:#f5f0e5;padding:10px 0;border-bottom:2px solid}article[hidden]{display:none}@media(max-width:650px){article{grid-template-columns:1fr}img{max-height:250px;width:100%}body{padding:16px}}</style>
<h1>Assets follow the design</h1><p>Atlas 01 / proposal / base 7722b45cb3dcee2fbcee26675fae4fef641cbba7.</p>
<p><b>Usable</b> means only the stated review purpose. <b>Revise</b> means seen but changes or closer inspection are needed. <b>Missing</b> means no judged usable exemplar for this design, even if bytes exist elsewhere. Pictures marked AI are targets, not evidence that the asset exists. Primitive entries are placement components, never unique asset counts.</p>
<p>P0: Mickey's and immediate street. P1: inhabited street detail. P2: town-wide production after visual approval. Engine integration is a separate status in every row.</p>
<nav><input id="q" placeholder="Find ID or object" aria-label="Find ID or object"><select id="p" aria-label="Priority"><option value="all">All priorities</option><option value="0">P0 Mickey's first</option><option value="1">P1 street detail</option><option value="2">P2 wider town</option></select><span id="count"></span></nav>'''+''.join(cards)+'''
<script>const q=document.querySelector('#q'),p=document.querySelector('#p');function filter(){let n=0;document.querySelectorAll('article').forEach(a=>{a.hidden=!(a.dataset.search.toLowerCase().includes(q.value.toLowerCase())&&(p.value==='all'||p.value===a.dataset.priority));if(!a.hidden)n++});document.querySelector('#count').textContent=n+' rows'}q.oninput=filter;p.onchange=filter;filter()</script></html>'''
(R/'assets.html').write_text(doc,encoding='utf-8');print('Wrote assets.html with',len(cards),'illustrated rows')
