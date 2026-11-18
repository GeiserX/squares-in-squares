"""Check the extra box's numerical runtime before enabling its four slots."""
from pathlib import Path
import subprocess,json,hashlib,sys,time
R=Path.home()/'scratch/squares-k123';runtime=json.load((R/'runtime33.json').open());PY=runtime['python'];fq=runtime['fq'];controls=[]
for loosen in [1.001,1.005]:
 dest=R/('control444-'+str(loosen))
 r=subprocess.run([PY,'-I','lane/k123_turn.py','444-control.csv','444',str(dest),fq,'--turns=0','--modes','self','--loosen',str(loosen),'--keep'],cwd=R,capture_output=True,text=True,timeout=180)
 (R/'out'/('control444-'+str(loosen)+'.log')).write_text(r.stdout+r.stderr);r.check_returncode()
 rows=[l for l in (dest/'turn-444.tsv').read_text().splitlines() if not l.startswith('#')];side=float(rows[-1].split('\t')[3]);assert abs(side-21.564693167754)<1e-7,side;controls.append({'loosen':loosen,'side':side})
import scipy,numpy
assert scipy.__version__=='1.18.1'
record={'time':time.strftime('%FT%TZ',time.gmtime()),'controls':controls,'fq_sha256':hashlib.sha256(Path(fq).read_bytes()).hexdigest(),'scipy':scipy.__version__,'numpy':numpy.__version__,'python':sys.version,'queued_pools':len(json.load((R/'boxD-pools33.json').open()))}
assert record['queued_pools']>0
(R/'boxD-control33.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
