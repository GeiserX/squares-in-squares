import pathlib,json,csv,subprocess,sys,hashlib,datetime
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
sys.path.insert(0,str(W));import controller23 as controller
sys.path.insert(0,str(controller.R));import floatsafe
jobs=json.load(open(W/'jobs.json'));specs=[]
for j in jobs:
 p=W/'boxE-raw'/j['id'];dp=p/'done.json'
 if not dp.exists()or j['kind']=='control':continue
 d=json.load(open(dp))
 if not d.get('quench_from_certified'):continue
 if ': near build recorded by 'in j['source']:
  original=S/j['source'].split(': near build recorded by ')[0]
  if original.exists():j['source'],j['licence']=controller.provenance(original,j['n'])
 specs.append(str(p/'final')+'|invent_rest.py lkick, family squeeze'+(' and fq'if j['fq']else'')+', then floatsafe and one fq quench from the certified file, from '+j['source']+'|'+j['licence'])
controller.atomic(W/'jobs.json',jobs);controller.atomic(W/'cert-specs.json',specs)
p=subprocess.run([sys.executable,'-I',str(W/'certrest23.py'),str(T),'@'+str(W/'cert-specs.json')],capture_output=True,text=True,check=True)
(W/'cert-final.log').write_text(p.stdout+p.stderr)
verification=[]
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);p=T/f'{n}.csv';rs=list(csv.DictReader(open(p)))
 assert len(rs)==n
 score,why=floatsafe.check(n,rs);pdscore,pdwhy=floatsafe.check(n,floatsafe.via_pandas(rs));gap=floatsafe.clearance(rs)
 assert why==pdwhy=='ok' and gap>=floatsafe.MIN_CLEARANCE,(n,why,pdwhy,gap)
 assert abs(score-float(row['new']))<1e-12,(n,score,row['new'])
 verification.append(dict(n=n,score=score,pandas_score=pdscore,clearance=gap,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(W/'verification.json').write_text(json.dumps(verification,indent=2))
print(json.dumps({'retained':len(verification),'min_clearance':min((r['clearance']for r in verification),default=None),'n':[r['n']for r in verification]}))
with open(T/'STATE.txt','a')as h:h.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA CERT final candidate pass: '+str(len(verification))+' rows, uncached metric/pandas and2.2e-11 clearance verified. Logwork/cert-final.log andwork/verification.json; take freeze18:40Z.\n')
