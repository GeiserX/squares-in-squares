"""Use the harvest lane's current public-only audit without changing its code."""
from pathlib import Path
import csv,functools,importlib.util,sys,time,hashlib
sys.dont_write_bytecode=True
import numpy as np
P=Path('tools/harvest31/policy.py')
_module=None
_code_stamp=None
_checked=0.
_stamp=None
def policy():
 global _module,_checked,_stamp,_code_stamp
 code_stamp=P.stat().st_mtime_ns
 if _module is None or code_stamp!=_code_stamp:
  name='k123_harvest_policy31';spec=importlib.util.spec_from_file_location(name,P);_module=importlib.util.module_from_spec(spec);sys.modules[name]=_module;spec.loader.exec_module(_module)
  frozen=Path('$SCRATCH/bounties-squares/take-assemble-r31/scripts/share31.py')
  fspec=importlib.util.spec_from_file_location('k123_frozen_share32',frozen);fm=importlib.util.module_from_spec(fspec);fspec.loader.exec_module(fm);fm.TOLS=(1e-6,1e-3,1e-2);_module._assembler=fm
  import json
  frozen_rows=json.load(open(Path(__file__).resolve().parent/'share/zips.json'))
  assert len(frozen_rows)==10,('frozen reference versions',len(frozen_rows))
  @functools.lru_cache(maxsize=1)
  def frozen_archive_paths36():
   paths=[]
   for name,want in frozen_rows:
    p=Path(name);assert hashlib.sha256(p.read_bytes()).hexdigest()==want,('changed frozen reference',name);paths.append(p)
   return tuple(paths)
  _module.archive_paths=frozen_archive_paths36
  _code_stamp=code_stamp;_checked=0.;_stamp=None
 if time.monotonic()-_checked>=300 or _stamp is None:
  _module.archive_paths.cache_clear()
  stamp=(code_stamp,tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in _module.archive_paths()))
  if _stamp is not None and stamp!=_stamp:
   _module.references.cache_clear();_module.excluded.cache_clear();_module.REFERENCE_ANGLES.clear()
  _stamp=stamp;_checked=time.monotonic();_module._k123_reference_stamp=stamp
 return _module

_measure_cache31={}
def measure(n,A):
 module=policy();A=np.ascontiguousarray(A,dtype=np.float64)
 identity=(n,hashlib.sha256(A.tobytes()).hexdigest(),module._k123_reference_stamp)
 if identity in _measure_cache31:return _measure_cache31[identity]
 rows=[dict(n=str(n),x=str(row[0]),y=str(row[1]),angle=str(row[2]) if len(row)>2 else '0') for row in A]
 ok,evidence=module.audit(rows)
 result=(max((e['share1e6'] for e in evidence),default=0.),max((e['share1e3'] for e in evidence),default=0.),max((e['share1e2'] for e in evidence),default=0.),min((float(e['maxd']) for e in evidence if isinstance(e.get('maxd'),(int,float))),default=float('inf')))
 _measure_cache31[identity]=result
 return result

def file_measure(path,n):
 rows=[r for r in csv.DictReader(open(path)) if int(r['n'])==n];ok,evidence=policy().audit(rows)
 return (max((e['share1e6'] for e in evidence),default=0.),max((e['share1e3'] for e in evidence),default=0.),min((float(e['maxd']) for e in evidence if isinstance(e.get('maxd'),(int,float))),default=float('inf')),max((e['share1e2'] for e in evidence),default=0.))
