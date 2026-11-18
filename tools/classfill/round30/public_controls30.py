from common29 import *
from public_review30 import review
results={}
for label,refs in [('own',[]),('valid793',[('jazivxt/boxed-in-sub',793)]),('excluded750',[('jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch',750)])]:
 p=W/(label+'-public-control.json');atomic(p,dict(source=('control '+str(S/'take-harvest-r27/work/public02/data/nb/jazivxt__boxed-in-sub/submission.csv') if label=='valid793' else 'control'),snapshots=[],expanded=dict(history=dict(public=refs))))
 r=review(p);results[label]=dict(complete=r['complete'],excluded=r['excluded'],variants=[(q['ref'],q['n'],len(q['variants']))for q in r['roots']]);print(label,results[label],flush=True)
assert results['own']['complete'] and results['valid793']['complete'] and results['excluded750']['excluded'] and not results['excluded750']['complete']
atomic(W/'public-controls30.json',dict(passed=True,results=results));note('CONTROL public preflight accepted own and notebook793; excluded fetched750 rejected before numerical admission.')
