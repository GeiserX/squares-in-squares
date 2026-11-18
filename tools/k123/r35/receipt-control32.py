from pathlib import Path
import sys,csv,json,shutil,time
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from publication_source26 import check
D=W/'receipt-control32';D.mkdir(exist_ok=True);p=D/'985.csv';shutil.copy(S/'take-k123-r29/985.csv',p)
r=next(r for r in csv.DictReader((S/'take-k123-r29/take.tsv').open(),delimiter='\t') if r['n']=='985')
audit=next((W/'admission-probes32').glob('eda16*/admission-check32.json'));rr={**r,'source':r['source']+'; diagnostic admission receipt '+str(audit)}
a=check(p,rr);assert a['clean'],a
b=check(p,{**rr,'source':rr['source']+'; actual input prvsiyan/squares-verified-best-of-1105'});assert not b['clean'],b
out={'diagnostic_receipt_ignored':a['clean'],'explicit_forbidden_source_refused':not b['clean'],'walked_files':a['files']};(W/'receipt-control32.json').write_text(json.dumps(out));print(json.dumps(out),flush=True)
