from pathlib import Path
import sys,csv,json,shutil,time
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from publication_source26 import check
D=W/'warm-control30';D.mkdir(exist_ok=True);p=D/'985.csv';shutil.copy(S/'take-k123-r29/985.csv',p)
r=next(r for r in csv.DictReader((S/'take-k123-r29/take.tsv').open(),delimiter='\t') if r['n']=='985');meta=D/'parent.json';meta.write_text(json.dumps(r));probe={'n':'985','source':'own join; source_record '+str(meta),'licence':r['licence']}
results=[]
for name,change,expect in [('initial',None,True),('warm',None,True),('changed-producer','recorded input prvsiyan/squares-verified-best-of-1105',False),('restored',r['source'],True)]:
 if change is not None:meta.write_text(json.dumps({**r,'source':change}))
 t=time.time();result=check(p,probe);assert result['clean']==expect,(name,result);results.append({'name':name,'clean':result['clean'],'seconds':time.time()-t,'files':result['files']})
(W/'warm-controls30.json').write_text(json.dumps(results,indent=2));print(json.dumps(results),flush=True)
