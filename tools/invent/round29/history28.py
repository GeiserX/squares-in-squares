import pathlib,json,csv,os,sys,runpy,time
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
W=pathlib.Path(__file__).resolve().parent;S=W.parents[1];sys.path.insert(0,str(W))
runpy.run_path(str(W/'invent_shape22.py'),run_name='__main__')
from invent_shape22 import fingerprint
import numpy as np
seen=set();count=0
for rnd in range(21,29):
 old=S/f'take-invent-r{rnd}/work'
 try:jobs=json.load(open(old/'jobs.json'))
 except (OSError,ValueError):continue
 for j in jobs:
  if j['kind']=='control'or not(old/'boxE-raw'/j['id']/'done.json').is_file():continue
  p=pathlib.Path(j['start']);p=p if p.is_absolute()else old/p
  try:
   rows=list(csv.DictReader(open(p)));a=np.array([[float(v['x']),float(v['y']),float(v['angle'])]for v in rows]);seen.add(fingerprint(a));count+=1
  except (OSError,ValueError,KeyError):pass
p=W/'historical-fingerprints.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(sorted(seen)));q.replace(p)
value=dict(files=count,distinct_geometry=len(seen));(W/'history-summary.json').write_text(json.dumps(value));print(json.dumps(value),flush=True)
with (W.parent/'STATE.txt').open('a')as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' HISTORY AUDIT completed immutable starts only: '+json.dumps(value)+'. Canonical translation/rotation/reflection control passed; moved square refused equivalence. Pending old starts are not closed unless their geometry actually ran.\n')
