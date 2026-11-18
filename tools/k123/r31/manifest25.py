import pathlib,hashlib,json
R=pathlib.Path.home()/'scratch/squares-k123'
out={}
for p in sorted(R.rglob('*')):
 if not p.is_file() or p.name=='manifest25.json':continue
 with open(p,'rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 out[str(p.relative_to(R))]={'bytes':p.stat().st_size,'sha256':sha}
(R/'manifest25.json').write_text(json.dumps(out))
print(json.dumps({'files':len(out),'bytes':sum(r['bytes'] for r in out.values())}))
