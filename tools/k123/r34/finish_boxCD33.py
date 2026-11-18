"""Stop, copy and checksum the extra box before removing only our scratch."""
from pathlib import Path
import sys,json,hashlib,subprocess,time
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));import finish26 as f
if (W/'boxCD-scratch-removed33.json').exists():
 receipt=json.load((W/'boxCD-copy-verified33.json').open());assert not receipt['checksum_differences'];print('verified boxD cleanup already complete');raise SystemExit
SSH=['ssh','-S','/tmp/squares-k123-r34-boxD','boxD'];PY=str(W.parent.parent/'venv/bin/python');f.SSH=SSH
f.run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-quench/venv/bin/python -I stop_remote25.py'],timeout=60)
f.run([PY,str(W/'bridge_boxCD33.py'),'--once','--no-export'],timeout=180)
f.run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-quench/venv/bin/python -I manifest25.py'],timeout=120)
D=W/'boxD-final';f.archive_copy(D);manifest=json.load((D/'manifest25.json').open());bad=[]
for name,r in manifest.items():
 p=D/name
 if not p.is_file() or p.stat().st_size!=r['bytes'] or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=r['sha256']:bad.append(name)
receipt={'files':len(manifest),'bytes':sum(r['bytes'] for r in manifest.values()),'checksum_differences':bad};(W/'boxCD-copy-verified33.json').write_text(json.dumps(receipt,indent=2));assert not bad,bad
assert not json.load((D/'processes-stopped25.json').open())['remaining']
f.run(SSH+['test -d $SCRATCH/squares-k123 && rm -rf -- $SCRATCH/squares-k123'],timeout=60)
(W/'boxCD-scratch-removed33.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'sha256_verified':True}))
f.run(['ssh','-S','/tmp/squares-k123-r34-boxD','-O','exit','boxD'],timeout=30,check=False)
print(json.dumps(receipt),flush=True)
