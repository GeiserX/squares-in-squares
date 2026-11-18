import pathlib,hashlib,json
R=pathlib.Path.home()/'scratch/squares-k123';out={}
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='manifest24.json':out[str(p.relative_to(R))]=dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest())
(R/'manifest24.json').write_text(json.dumps(out));print('manifest files',len(out),'bytes',sum(r['bytes'] for r in out.values()))
