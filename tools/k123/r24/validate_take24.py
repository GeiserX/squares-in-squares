import pathlib,sys,csv,json,math
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'));import floatsafe
from seed_notice24 import notice
from provenance24 import banned
csv.field_size_limit(20000000);report=[]
for row in csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t'):
 n=int(row['n']);rows=list(csv.DictReader(open(W.parent/f'{n}.csv')));_,fr,score,error=floatsafe.work((n,rows));label,flag,ns=notice(row['source'],row['licence']);ok=fr is not None and abs(score-float(row['new']))<1e-13 and flag is not None and not banned(row['source']+' '+row['licence']);report.append(dict(n=n,score=score,saved=float(row['new']),valid=ok,samanyu=flag,seed_n=ns,error=error));print(n,'valid',ok,'score',score,'samanyu',flag,flush=True)
(W/'take-validation24.json').write_text(json.dumps(report,indent=2));assert all(r['valid'] for r in report)
