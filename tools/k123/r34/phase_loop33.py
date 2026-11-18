from pathlib import Path
import time,runpy,sys,os,traceback
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
while time.time()<float((W/'search-deadline').read_text()):
 try:runpy.run_path(str(W/'feed_phase33.py'),run_name='__main__')
 except SystemExit:pass
 except Exception:traceback.print_exc()
 if (W/'phase-feed33.json').exists():
  import json
  s=json.load((W/'phase-feed33.json').open())
  if s.get('halted') or len(s['jobs'])>=6 and all(j.get('collected') for j in s['jobs']):break
 time.sleep(30)
