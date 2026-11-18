from pathlib import Path
import sys,json,csv,hashlib,shutil,importlib,time,re
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];sys.path.insert(0,'.');csv.field_size_limit(1<<28)
import quench_walk
from current_walk29 import configure
w=configure(importlib.reload(quench_walk));base=w.load_withdrawn
# Only test the false broad-classification notices named by the main07:34:54Z correction.
def false_notice(p,line):
 return p.startswith('take-forensics-r28/near/') and line.startswith('2026-11-15T01:51:44.') and 'explicit rule-a family in retained ancestry (r23 forensics donor745/858' in line
def load():
 base();w.WITHDRAWN_LINES[:]=[(p,l) for p,l in w.WITHDRAWN_LINES if not false_notice(p,l)]
w.load_withdrawn=load
D=W/'reopened-trap29';D.mkdir(exist_ok=True);out=[]
for n in [540,743]:
 src=S/f'take-midm-r28/{n}.csv';ledger=src.parent/'take.tsv';row=next(r for r in csv.DictReader(ledger.open(),delimiter='\t') if r['n']==str(n));data=src.read_bytes();sha=hashlib.sha256(data).hexdigest();dest=D/(str(n)+'-'+sha+'.csv');dest.write_bytes(data);Path(str(dest)+'.json').write_text(json.dumps(row))
 result=w.check(str(dest));rec={'n':n,'path':str(dest),'sha256':sha,'row':row,'walk':result};out.append(rec);print(n,result['clean'],result['hits'],flush=True)
(W/'trap-controls29.json').write_text(json.dumps(out,indent=2))
