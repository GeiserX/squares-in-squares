from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from snapshot_policy30 import hit
from walker30 import withdraw_time
r={'origin':str(W.parent/'near/fixture.csv'),'sha256':'a'*64,'origin_mtime':withdraw_time('2026-11-15T12:00:00Z')};p='take-k123-r30/near/fixture.csv'
a='2026-11-15T12:01:00Z k123 -> all: WITHDRAW '+p+' sha256 '+'a'*64
b=a.replace('a'*64,'b'*64)
assert hit(r,p,a,withdraw_time) and not hit(r,p,b,withdraw_time)
assert hit(r,p,'2026-11-15T12:01:00Z WITHDRAW '+p,withdraw_time)
assert not hit({**r,'origin_mtime':withdraw_time('2026-11-15T12:02:00Z')},p,'2026-11-15T12:01:00Z WITHDRAW '+p,withdraw_time)
assert hit({**r,'origin_mtime':withdraw_time('2026-11-15T12:02:00Z')},p,'2026-11-15T12:03:00Z WITHDRAW '+p,withdraw_time)
result={'withdrawn_exact_hash_rejected':True,'different_hash_preserved':True,'later_build_preserved':True,'later_action_rejected':True};(W/'snapshot-controls30.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
