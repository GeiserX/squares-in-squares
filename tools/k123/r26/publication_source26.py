"""Require the complete independent source walk before a row is published."""
import pathlib,json,hashlib,shutil,sys,importlib

def check(path,row):
 path=pathlib.Path(path)
 sys.path.insert(0,'.')
 import quench_walk
 walker=importlib.reload(quench_walk)
 payload={k:row.get(k,'') for k in ['n','source','licence']}
 digest=hashlib.sha256(path.read_bytes()+json.dumps(payload,sort_keys=True).encode()).hexdigest()
 probes=path.parent/'source-checks26';probes.mkdir(exist_ok=True)
 probe=probes/('source-walk-'+digest+'.csv')
 if not probe.exists():shutil.copy(path,probe)
 pathlib.Path(str(probe)+'.json').write_text(json.dumps(payload))
 result=walker.check(str(probe));result['csv_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 (path.parent/'source-walk26.json').write_text(json.dumps(result,indent=2))
 return result
