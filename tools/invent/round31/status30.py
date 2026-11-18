"""Print concise restart and progress evidence without starting numerical work."""
import csv,json,pathlib,time,subprocess
W=pathlib.Path(__file__).resolve().parent;T=W.parent
jobs=json.load(open(W/'jobs.json'));out=W/'boxE-raw'
ends={p.parent.name:json.load(open(p)) for p in out.glob('*/done.json')}
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
active=[]
for j in jobs:
 folder=out/j['id']
 if not folder.exists()or j['id']in ends:continue
 lines=[line for p in folder.glob('slide-*.tsv')for line in p.read_text().splitlines()if line and line[0].isdigit()]
 last=lines[-1].split('\t')if lines else []
 active.append(dict(n=j['n'],id=j['id'],raw=len(list((folder/'raw').glob('*.csv'))),trial=last[0]if last else None,side=last[3]if len(last)>3 else None,bar=j['bar']))
print(json.dumps(dict(time=time.strftime('%FT%TZ',time.gmtime()),queued=len(jobs),ended=len(ends),raw=sum(d.get('raw',0)for d in ends.values()),errors=[i for i,d in ends.items()if d.get('error')],active=active,rows=[dict(n=int(r['n']),gain=float(r['gain']))for r in rows],bar_control=(W/'BAR_CONTROL_GREEN').exists()),separators=(',',':')))
for name in ('controller','finish'):
 p=W/(name+'.pid')
 if p.exists():
  result=subprocess.run(['ps','-p',p.read_text().strip(),'-o','pid=,etime=,%cpu='],capture_output=True,text=True)
  print(name,result.stdout.strip()or 'STOPPED')
