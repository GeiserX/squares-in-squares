import pathlib,hashlib,json
W=pathlib.Path(__file__).resolve().parent;R=W/'boxE-final';manifest=json.load(open(R/'manifest24.json'));bad=[]
for name,record in manifest.items():
 p=R/name
 if not p.exists() or p.stat().st_size!=record['bytes'] or hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()!=record['sha256']:bad.append(name)
report=dict(files=len(manifest),bytes=sum(r['bytes'] for r in manifest.values()),checksum_differences=bad);(W/'copy-verified24.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert not bad
