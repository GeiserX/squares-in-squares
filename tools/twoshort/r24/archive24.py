"""Verify copied completed libraries before freeing their remote disk space."""
from pathlib import Path
import subprocess,json,hashlib,shlex,datetime
W=Path(__file__).parent;R=W/'boxE24'
code='''from pathlib import Path
import json,hashlib
r=Path.home()/"scratch/squares-twoshort";out=[]
for s in (r/"designs").glob("*/summary.json"):
 tag=s.parent.name;d=s.parent/"lib"
 if not tag.startswith(("library-zones-","library-modules-")) or d.is_symlink() or not d.is_dir():continue
 files={n:hashlib.sha256((d/n).read_bytes()).hexdigest() for n in ["library.pkl","lens.pkl"] if (d/n).exists()}
 if len(files)==2:out.append(dict(tag=tag,files=files,bytes=sum((d/n).stat().st_size for n in files)))
print(json.dumps(out))'''
r=subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(code)],check=True,capture_output=True,text=True,timeout=90);rows=json.loads(r.stdout);verified=[];pending=[]
for row in rows:
 d=R/'designs'/row['tag']/'lib'
 if all((d/n).exists() and hashlib.sha256((d/n).read_bytes()).hexdigest()==h for n,h in row['files'].items()):verified.append(row)
 else:pending.append(row)
if verified:
 code='''from pathlib import Path
import hashlib,shutil,json
r=Path.home()/"scratch/squares-twoshort/designs";rows='''+repr(verified)+'''
for row in rows:
 d=r/row["tag"]/"lib"
 assert d.is_dir() and not d.is_symlink()
 assert {n:hashlib.sha256((d/n).read_bytes()).hexdigest() for n in row["files"]}==row["files"]
 shutil.rmtree(d)
print(json.dumps(rows))'''
 result=subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(code)],check=True,capture_output=True,text=True,timeout=90)
 archive=W/'archive-checks.json';prior=json.load(open(archive)) if archive.exists() else [];prior+=json.loads(result.stdout);archive.write_text(json.dumps(prior,indent=2))
 for row in verified:(R/'designs'/row['tag']/'lib/copy-check.json').write_text(json.dumps(row,indent=2))
 with (W.parent/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA ARCHIVE verified '+str(len(verified))+' completed library pairs ('+str(sum(r['bytes'] for r in verified))+' bytes), then removed only those remote lib directories. Local copies and SHA256 receipts remain in work/boxE24/designs. Log work/archive-checks.json. Search/quench deadline22:15UTC.\n')
print(json.dumps(dict(removed_libraries=len(verified),freed_bytes=sum(r['bytes'] for r in verified),needs_copy=[r['tag'] for r in pending])),flush=True)
(W/'archive-needs-copy.json').write_text(json.dumps(pending,indent=2))
