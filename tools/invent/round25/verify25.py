"""Verify selected immutable boxE ends without a score cache."""
import csv,hashlib,json,pathlib,signal,sys,time
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D/'lane'))
import floatsafe
END=float((D/'deadline').read_text())
def timed_out(*unused):raise TimeoutError('common verification deadline reached')
signal.signal(signal.SIGALRM,timed_out);signal.alarm(max(1,int(END-time.time())))
def atomic(p,value):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(value,indent=2));q.replace(p)
def check(path,n,expected):
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 if digest!=expected:raise ValueError('CSV hash differs from completed receipt')
 rows=list(csv.DictReader(path.open()));assert len(rows)==n
 score,why=floatsafe.check(n,rows);pr=floatsafe.via_pandas(rows);pds,pdwhy=floatsafe.check(n,pr)
 gap=min(floatsafe.clearance(rows),floatsafe.clearance(pr))
 assert why==pdwhy=='ok' and gap>=2.2e-11,(path,why,pdwhy,gap)
 return dict(n=n,sha256=digest,score=score,pandas_score=pds,clearance=gap)
positive=[dict(n='2',square_id='0',x='.5',y='.5',angle='0'),dict(n='2',square_id='1',x='1.5001',y='.5',angle='0')]
assert floatsafe.check(2,positive)[1]=='ok'
negative=[dict(v)for v in positive];negative[1]['x']='.5';assert floatsafe.check(2,negative)[1]!='ok'
folder=D/'verification-control';folder.mkdir(exist_ok=True);p=folder/'2.csv'
with p.open('w',newline='')as h:
 w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(positive)
digest=hashlib.sha256(p.read_bytes()).hexdigest();check(p,2,digest)
try:check(p,2,'0'*64)
except ValueError:pass
else:raise AssertionError('mismatched receipt control passed')
print('CONTROL separated n2 accepted, overlap refused, changed receipt hash refused',flush=True)
controls=dict(separated_n2=True,overlap_refused=True,wrong_hash_refused=True)
result=dict(controls=controls,verified={},errors={},started=time.strftime('%FT%TZ',time.gmtime()))
output=D/'verification25.json';atomic(output,result)
for spec in json.load(open(D/'verify-specs.json')):
 if time.time()>END-5:break
 path=D/spec['file']
 try:
  proof=check(path,spec['n'],spec['sha256']);assert abs(proof['score']-spec['score'])<1e-12
  result['verified'][spec['file']]=proof
  print('VERIFIED',spec['file'],proof['score'],proof['clearance'],flush=True)
 except Exception as ex:
  result['errors'][spec['file']]=str(ex);print('REFUSED',spec['file'],str(ex),flush=True)
 atomic(output,result)
result['ended']=time.strftime('%FT%TZ',time.gmtime());atomic(output,result)
if result['errors']:raise SystemExit(1)
print('Finished',len(result['verified']),'uncached files',flush=True)
