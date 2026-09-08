"""Rebuild the complete portable file index; excludes only ephemeral caches and itself's output hash."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
files=sorted(p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.blend1'] and p.name!='INVENTORY.md')
rows=['# Commission file inventory','','All paths are relative to this directory. Text bytes and SHA-256 values use canonical LF line endings, matching the local .gitattributes and Git blobs. Binary bytes are unchanged. INVENTORY.md is this generated index; it is listed without its own hash to avoid self-reference.','','| File | Bytes | SHA-256 |','|---|---:|---|']
for p in files:
    rel=p.relative_to(R).as_posix();data=p.read_bytes()
    if p.suffix not in ['.png','.jpg']:data=data.replace(b'\r\n',b'\n')
    rows.append(f'| [{rel}]({rel}) | {len(data)} | {hashlib.sha256(data).hexdigest()} |')
rows.append('| INVENTORY.md | generated index | self-reference excluded |')
(R/'INVENTORY.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
print(len(files)+1,'commission files including this index')
