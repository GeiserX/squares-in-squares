"""Pair the new certified end with the exact non-winning donor that supplied it."""
from pathlib import Path
import sys,hashlib,json,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from stage24 import stage,current,mlp
P,o=current();path=W.parent/'near/367-threeway28-c1088e881b67bc2e.csv';A=mlp.load(str(path),{367})[367];raw=(W.parent/'295.csv').read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest=='8262a0387d745e4230c08da6d16f8e4d60f199c73fd05e3df61624d58e3a6344'
P[367]=A;o[367]=str(path);tag='freshreturn29530h'+digest[:8]
assert stage(tag,P,o,[(295,367)],'fresh-return','new certified295 joined with the exact non-winning367 donor that supplied it; changed295 geometry, same frozen367 input')
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START changed295/frozen367 return scan '+tag+' in existing boxE queue.367 was1.91076034312e-3 above its bar and supplied the1.3613760239117312e-6 score gain at295. New295 CSV is byte-pinned; numerical completed geometry remains closed. Deadline00:15Z.\n')
