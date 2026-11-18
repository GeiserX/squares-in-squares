from pathlib import Path
import sys,json,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from policy27 import banned
p='take-backlog-r26/near/972-backlog-withdrawn-gone-parent.csv'
assert not banned(json.dumps({'source':'held n = 972 of round 31','checked_paths':[p]}))
assert banned(json.dumps({'source':p}))
from source25 import audit
c=json.load((W/'fresh10023/sources-fresh10023.json').open())['972'];t=time.time();r=audit(c);assert r,'held972 must not be refused by checked_paths'
out={'diagnostic_withdrawn_path_ignored':True,'actual_source_withdrawn_path_refused':True,'held972_accepted':True,'seconds':time.time()-t};(W/'diagnostic-control32.json').write_text(json.dumps(out));print(json.dumps(out),flush=True)
