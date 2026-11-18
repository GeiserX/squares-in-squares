"""Require the complete independent source walk before a row is published."""
import pathlib,json,hashlib,shutil,sys,importlib

def check(path,row):
 path=pathlib.Path(path)
 sys.path.insert(0,'.')
 import quench_walk
 from current_walk29 import configure
 walker=configure(importlib.reload(quench_walk))
 payload={k:row.get(k,'') for k in ['n','source','licence']}
 digest=hashlib.sha256(path.read_bytes()+json.dumps(payload,sort_keys=True).encode()).hexdigest()
 probes=path.parent/'source-checks26';probes.mkdir(exist_ok=True)
 probe=probes/('source-walk-'+digest+'.csv')
 if not probe.exists():shutil.copy(path,probe)
 pathlib.Path(str(probe)+'.json').write_text(json.dumps(payload))
 result=walker.check(str(probe))
 from seed_rule27 import file_checks
 checks=file_checks(probe,walker);result['original_seed_checks']=checks
 for z in checks:
  if z['excluded']:result['hits'].append('original seed%d prvsiyan share %.12g >=0.4' % (z['n'],z['share']));result['clean']=False
 from csv_rule27 import file_checks as csv_checks
 whole=csv_checks(probe,walker);result['complete_csv_ancestor_checks']=whole
 for z in whole:
  if z['excluded']:result['hits'].append('complete ancestor n%d prvsiyan share %.12g >=0.4: %s' % (z['n'],z['share'],z['path']));result['clean']=False
 result['csv_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 (path.parent/'source-walk26.json').write_text(json.dumps(result,indent=2))
 return result
