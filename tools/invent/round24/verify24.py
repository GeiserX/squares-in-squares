import csv,json,pathlib,time,sys,hashlib,signal,math
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D/'lane'));import floatsafe
END=float((D/'deadline').read_text());signal.signal(signal.SIGALRM,lambda *a:sys.exit(0));signal.alarm(max(1,int(END-time.time())))
def atomic(name,value):
 p=D/name;q=p.with_suffix('.tmp');q.write_text(json.dumps(value));q.replace(p)
def numeric(rows):return hashlib.sha256(json.dumps([[int(r['n']),int(r['square_id']),*[float(r[k])for k in ('x','y','angle')]]for r in rows],separators=(',',':')).encode()).hexdigest()
valid=[dict(n='2',square_id='0',x='0.5',y='0.5',angle='0'),dict(n='2',square_id='1',x='1.5001',y='0.5',angle='0')]
sc,why=floatsafe.check(2,valid);assert why=='ok';bad=[dict(r)for r in valid];bad[1]['x']='0.5';assert floatsafe.check(2,bad)[1]!='ok'
print('CONTROL metric accepted separated n2 and rejected duplicate overlap',flush=True)
verified={};atomic('uncached-verification.json',verified)
while time.time()<END-5:
 receipts={}
 for p in D.glob('*/final/*.csv'):
  dp=p.parent.parent/'done.json'
  if not dp.exists():continue
  try:d=json.load(open(dp))
  except ValueError:continue
  if not d.get('quench_from_certified'):continue
  receipts[str(p.relative_to(D))]=dict(n=int(p.stem),score=d['new'],sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 atomic('certified-receipts.json',receipts)
 for rel,r in receipts.items():
  if rel in verified and verified[rel]['sha256']==r['sha256']:continue
  if time.time()>END-10:break
  rows=list(csv.DictReader(open(D/rel)));n=r['n'];score,why=floatsafe.check(n,rows);pdscore,pdwhy=floatsafe.check(n,floatsafe.via_pandas(rows));gap=floatsafe.clearance(rows)
  assert why==pdwhy=='ok' and gap>=floatsafe.MIN_CLEARANCE and abs(score-r['score'])<1e-12,(rel,why,pdwhy,gap,score,r['score'])
  verified[rel]=dict(r,pandas_score=pdscore,clearance=gap,numeric_hash=numeric(rows));atomic('uncached-verification.json',verified)
  print('VERIFIED',rel,score,gap,flush=True)
 time.sleep(2)
print('Finished',len(verified),flush=True)
