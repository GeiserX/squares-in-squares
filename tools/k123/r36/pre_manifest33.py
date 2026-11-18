"""Inventory only owned scratch for a verified incremental pre-copy."""
from pathlib import Path
import json,hashlib
R=Path.home()/'scratch/squares-k123';out={}
for p in sorted(R.rglob('*')):
 if not p.is_file() or p.name=='pre-manifest33.json':continue
 try:
  st=p.stat();sha=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();post=p.stat()
 except FileNotFoundError:continue
 if (st.st_size,st.st_mtime_ns)!=(post.st_size,post.st_mtime_ns):continue
 out[str(p.relative_to(R))]={'bytes':st.st_size,'sha256':sha,'mtime_ns':st.st_mtime_ns}
(R/'pre-manifest33.json').write_text(json.dumps(out));print(json.dumps({'files':len(out),'bytes':sum(z['bytes'] for z in out.values())}))
