from pathlib import Path
import sys,json,csv,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from current_walk29 import lifted_pair,TARGET
assert lifted_pair(TARGET,'2026-11-13T23:17:11Z old Samanyu-only notice')
assert lifted_pair(TARGET,'2026-11-14T01:27:36Z old Samanyu-only notice')
assert not lifted_pair(TARGET,'2026-11-15T08:00:00Z later overlap withdrawal')
assert not lifted_pair('take-other-r17/near/921-29e12ff3.csv','2026-11-13T23:17:11Z same timestamp other path')
from publication_source26 import check
out=[]
for key,expect in [('j22c-fresh10401-804-985-j9-10-s0',True),('j22a-fresh10238-551r-599-j8-10-s-1',False)]:
 D=W/'certs'/key;sub='out' if expect else 'final';row=next(csv.DictReader((D/sub/'take.tsv').open(),delimiter='\t'))
 # The final551 check uses the restored source supplied to the verifier, not the old absent-producer text.
 if not expect:row['source']=json.load((W/'collect-state.json').open())[key]['source']
 result=check(D/sub/(row['n']+'.csv'),row);out.append({'key':key,'clean':result['clean'],'hits':result['hits']});assert result['clean']==expect,out
(W/'walk-controls29.json').write_text(json.dumps({'exact_pair_controls':True,'later_withdrawal_preserved':True,'rows':out},indent=2));print(json.dumps(out),flush=True)
