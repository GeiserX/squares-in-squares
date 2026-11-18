"""Require every boxE CSV to match its local copy before acknowledging transfer."""
import hashlib,json,pathlib,sys,tempfile,time
W=pathlib.Path(__file__).resolve().parent

def matches(path,wanted):
 return path.is_file()and hashlib.sha256(path.read_bytes()).hexdigest()==wanted

with tempfile.TemporaryDirectory(dir=W)as folder:
 p=pathlib.Path(folder)/'control.csv';p.write_bytes(b'n,x\n2,1\n');digest=hashlib.sha256(p.read_bytes()).hexdigest()
 assert matches(p,digest);p.write_bytes(b'n,x\n2,2\n');assert not matches(p,digest)
 assert not matches(p.parent/'missing.csv',digest)
print('CONTROL exact transfer accepted; changed and missing copies refused',flush=True)
if '--controls'in sys.argv:raise SystemExit(0)
manifest=W/'boxE-raw/csv-manifest.json';items=json.load(open(manifest));bad=[]
for ref,digest in items.items():
 rel=pathlib.PurePosixPath(ref);assert not rel.is_absolute()and '..'not in rel.parts
 path=W/rel if rel.parts[0]=='starts'else W/'boxE-raw'/rel
 if not matches(path,digest):bad.append(dict(remote=ref,local=str(path)))
result=dict(time=time.strftime('%FT%TZ',time.gmtime()),files=len(items),manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),mismatches=bad)
(W/'transfer-check.json').write_text(json.dumps(result,indent=2));assert not bad,bad
(W/'TRANSFER_OK.json').write_text(json.dumps({k:result[k]for k in ('files','manifest_sha256')},indent=2))
print(json.dumps(result))
