"""Build an immutable verification list from completed source-admitted ends."""
import hashlib,json,pathlib,time,sys,csv
W=pathlib.Path(__file__).resolve().parent
specs=[];reject=[]
for j in json.load(open(W/'jobs.json')):
 if j['kind']=='control':continue
 folder=W/'boxE-raw'/j['id'];p=folder/'final'/f'{j["n"]}.csv'
 if not p.exists()or not(folder/'done.json').exists():continue
 d=json.load(open(folder/'done.json'));proof=json.load(open(j['ancestry']))if j.get('ancestry')else{}
 if proof.get('policy')!='strict28v1'or not proof.get('ok')or not d.get('quench_from_certified'):reject.append(j['id']);continue
 digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==d['sha256']
 specs.append(dict(file=j['id']+'/final/'+str(j['n'])+'.csv',n=j['n'],sha256=digest,score=d['new']))
if '--competitive'in sys.argv:
 base={int(row['n']):float(row['bar'])for row in csv.DictReader(open(W.parent.parent/'round28-briefs/bar28.tsv'),delimiter='\t')}
 specs=[spec for spec in specs if spec['score']<base[spec['n']]-1e-10]
specs.sort(key=lambda v:(v['n'],v['score'],v['file']))
p=W/'verify-specs.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(specs,indent=2));q.replace(p)
(W/'verification-admission.json').write_text(json.dumps(dict(time=time.strftime('%FT%TZ',time.gmtime()),admitted=len(specs),refused=reject),indent=2))
print(json.dumps(dict(admitted=len(specs),refused=len(reject))))
