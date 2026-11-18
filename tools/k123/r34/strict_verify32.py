from pathlib import Path
import sys,csv,json,hashlib,time
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W),'.'];sys.dont_write_bytecode=True;csv.field_size_limit(1<<28)
import strict_walk32 as walk
out=[]
for r in csv.DictReader((T/'take.tsv').open(),delimiter='\t'):
 n=int(r['n']);p=T/f'{n}.csv';before=hashlib.sha256(p.read_bytes()).hexdigest();t=time.time();result=walk.check(str(p));assert before==hashlib.sha256(p.read_bytes()).hexdigest();out.append({'n':n,'sha256':before,'clean':result['clean'],'hits':result['hits'],'files':result['files'],'seconds':time.time()-t});(W/'strict-validation32.json').write_text(json.dumps(out,indent=2));print(json.dumps(out[-1]),flush=True)
(W/'strict-validation32.json').write_text(json.dumps(out,indent=2))

assert all(r['clean'] for r in out),[(r['n'],r['hits']) for r in out if not r['clean']]
