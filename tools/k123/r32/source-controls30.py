from pathlib import Path
import sys,json,csv,shutil
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from publication_source26 import check
from current_walk29 import lifted_pair,TARGET
assert lifted_pair(TARGET,'2026-11-13T23:17:11Z old seed notice')
assert not lifted_pair(TARGET,'2026-11-15T12:00:00Z later actual withdrawal')
D=W/'source-control30';D.mkdir(exist_ok=True)
old=S/'take-k123-r29';r=next(r for r in csv.DictReader((old/'take.tsv').open(),delimiter='\t') if r['n']=='985');p=D/'985.csv';shutil.copy(old/'985.csv',p);a=check(p,r);assert a['clean'],a
p0=S/'take-harvest-r22/work/collector/certified/52c2828aaa9bb34a242993b087e32c929e345b516309882921072b62a2365102.csv';p=D/'551.csv';shutil.copy(p0,p)
r={'n':'551','source':'kmmmvs/squares-public-merge-daily :: submission.csv; fetched public-first source '+str(p0),'licence':'Apache 2.0'};b=check(p,r);assert not b['clean'],b
result={'own985_passes':a['clean'],'own985_files':a['files'],'fetched551_rejected':not b['clean'],'fetched551_hits':b['hits'],'later_withdrawal_preserved':True};(W/'source-controls30.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
