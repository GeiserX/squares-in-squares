from common29 import *
from publishgate29 import check
import resource
resource.setrlimit(resource.RLIMIT_CPU,(170,180))
for row in rows(T/'take.tsv'):
 n=int(row['n']);sha=hashlib.sha256((T/f'{n}.csv').read_bytes()).hexdigest();ap=next(p for p in (W/'audited').glob('*.json') if read(p,{}).get('certified_output_sha256')==sha);a=read(ap)
 inputs=list((W/'inputs').glob(f'{n}-{a["tag"]}.csv'));start=time.time();r=check(a['tag'],n,a['input_proof'],inputs[0],seconds=180)
 atomic(W/f'extended-source-{n}.json',r)
 if r.get('clean'):a['independent_source_check']=r;atomic(ap,a)
 note(f'EXTENDED_SOURCE n{n} seconds{time.time()-start:.3f} clean{r.get("clean")} hits'+json.dumps(r.get('hits',[]))[:900]);print(n,time.time()-start,r.get('clean'),r.get('files'),r.get('hits',[])[:8],r.get('gone',[])[:5],flush=True)
