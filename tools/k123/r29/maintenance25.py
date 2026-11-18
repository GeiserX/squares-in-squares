import time,runpy
from provenance24 import W
p=W/'revoke-last'
if not p.exists() or time.time()-p.stat().st_mtime>480:
 runpy.run_path(str(W/'revoke25.py'),run_name='__main__');p.touch()
