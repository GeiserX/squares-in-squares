"""Check the immutable take bytes through direct and pandas float readers."""
from pathlib import Path
import csv,json,hashlib,sys,time
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W/'lane')];csv.field_size_limit(1<<28)
import floatsafe
checks=[]
for row in csv.DictReader((T/'take.tsv').open(),delimiter='\t'):
 n=int(row['n']);p=T/f'{n}.csv';digest=hashlib.sha256(p.read_bytes()).hexdigest();raw=list(csv.DictReader(p.open()));parsed=floatsafe.via_pandas(raw)
 a=floatsafe.check(n,raw);b=floatsafe.check(n,parsed);g0=floatsafe.clearance(raw);g1=floatsafe.clearance(parsed)
 assert a[1]=='ok' and b[1]=='ok' and min(g0,g1)>=2e-11,(n,a,b,g0,g1)
 assert abs(a[0]-float(row['new']))<1e-13 and abs(b[0]-float(row['new']))<1e-13,(n,a,b,row['new'])
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
 checks.append({'n':n,'sha256':digest,'raw_score':a[0],'pandas_score':b[0],'raw_clearance':g0,'pandas_clearance':g1,'unchanged':True});print(json.dumps(checks[-1]),flush=True)
(W/'independent33.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'checks':checks},indent=2))
