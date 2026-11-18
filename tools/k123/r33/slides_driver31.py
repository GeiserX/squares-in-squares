"""Keep the controlled model feeder independent of long source-admission passes."""
from pathlib import Path
import os,sys,time,runpy,traceback,gc
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];os.chdir(W)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',K123_SOURCE_BUDGET30='1')
while time.time()<float((W/'search-deadline').read_text())-700:
 try:
  result=runpy.run_path(str(W/'feedslides31.py'),run_name='__main__')
  if result.get('feedlock'):result['feedlock'].close()
  del result
 except SystemExit:pass
 except Exception:traceback.print_exc()
 gc.collect();time.sleep(30)
