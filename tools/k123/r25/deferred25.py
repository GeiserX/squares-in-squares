import pathlib,time
from provenance24 import W
from stage24 import deferred
p=W/'deferred-last'
if not p.exists() or time.time()-p.stat().st_mtime>900:
 p.touch();deferred(2)
