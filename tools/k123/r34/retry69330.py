from pathlib import Path
import sys,json,csv,hashlib,fcntl,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from bind_row30 import bind
from publication_source26 import check
key='j22a-resume30resume29deferred28f0525b38e3x108-455r-693-j12-12-s0';pool='resume30resume29deferred28f0525b38e3x108';D=W/'certs'/key;row=next(csv.DictReader((D/'out/take.tsv').open(),delimiter='\t'));meta=json.load((W/pool/f'sources-{pool}.json').open());row['licence']='own join; '+' | '.join(meta[str(n)]['licence'] for n in [455,693]);before=hashlib.sha256((D/'out/693.csv').read_bytes()).hexdigest();new=bind(row,meta,[455,693],pool,key+'-initial');result=check(D/'out/693.csv',new);assert result['clean'],result;assert before==hashlib.sha256((D/'out/693.csv').read_bytes()).hexdigest()
lock=(W/'collect.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX);p=W/'collect-state.json';states=json.load(p.open());assert states[key]['status']=='source-refused';states.pop(key);p.with_suffix('.tmp').write_text(json.dumps(states));p.with_suffix('.tmp').replace(p)
record={'key':key,'certificate_sha256':before,'source_clean':True,'files':result['files'],'missing':result.get('missing',[]),'hits':result['hits'],'score':row['new'],'gain':row['gain']};(W/'retry693-control30.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH693 binding repair: exact content-addressed proof aliases replace only complete paths and standalone digests. Full source walk passes; CSV unchanged '+before+'. Retry initial certificate through the normal certified-file quench before any publication. Deadline07:25Z.\n')
