import pathlib,json,csv,subprocess,sys,hashlib,datetime
csv.field_size_limit(16*1024*1024)
W=pathlib.Path(__file__).resolve().parent;T=W.parent;sys.path.insert(0,str(W))
from ancestry24 import clean
js=json.load(open(W/'jobs.json'));specs=[]
receipts=json.load(open(W/'boxE-raw/certified-receipts.json'));verified=json.load(open(W/'boxE-raw/uncached-verification.json'))
cache={};numeric={r['numeric_hash']:r for r in verified.values()}
for j in js:
 p=W/'boxE-raw'/j['id'];dp=p/'done.json';f=p/'final'/f"{j['n']}.csv";rel=f"{j['id']}/final/{j['n']}.csv"
 if not dp.exists() or not f.exists() or j['kind']=='control' or not clean(j['source'],j['licence'])[0]:continue
 d=json.load(open(dp));r=receipts.get(rel)
 if not d.get('quench_from_certified') or not r:continue
 digest=hashlib.sha256(f.read_bytes()).hexdigest();assert digest==r['sha256'] and abs(d['new']-r['score'])<1e-14
 cache[str(f)]=[f.stat().st_mtime,r['score'],digest,True]
 specs.append(str(p/'final')+'|invent_rest.py lkick, family squeeze'+(' and fq'if j['fq']else'')+', then floatsafe and one fq quench from the certified file, from '+j['source']+'|'+j['licence'])
(W/'fs-cache-policy.json').write_text(json.dumps(cache));(W/'cert-specs.json').write_text(json.dumps(specs))
p=subprocess.run([sys.executable,'-I',str(W/'certrest24.py'),str(T),'@'+str(W/'cert-specs.json')],capture_output=True,text=True,check=True)
(W/'cert-final.log').write_text(p.stdout+p.stderr);out=[]
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);f=T/f'{n}.csv';rs=list(csv.DictReader(open(f)));key=hashlib.sha256(json.dumps([[int(r['n']),int(r['square_id']),*[float(r[k])for k in ('x','y','angle')]]for r in rs],separators=(',',':')).encode()).hexdigest()
 r=numeric.get(key);assert r is not None,('missing uncached boxE verification',n)
 assert len(rs)==n and abs(r['score']-float(row['new']))<1e-12 and r['clearance']>=2.2e-11
 out.append(dict(n=n,score=r['score'],pandas_score=r['pandas_score'],clearance=r['clearance'],sha256=hashlib.sha256(f.read_bytes()).hexdigest(),numeric_hash=key,verified_on='boxE',proof='boxE-raw/uncached-verification.json'))
(W/'verification.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'retained':len(out),'min_clearance':min((r['clearance']for r in out),default=None),'n':[r['n']for r in out]}))
with open(T/'STATE.txt','a')as h:h.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA CERT final rebuild from hash-matched completed boxE floatsafe/quench receipts. Selected layouts match uncached officialmetric/pandas/clearance proofs on boxE. Take final22:25Z.\n')
