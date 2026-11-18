from pathlib import Path
import json,collections,csv,time
W=Path(__file__).resolve().parent;T=W.parent
try:r=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()]
except (OSError,ValueError):r=[]
try:state=json.loads((W/'collect-state.json').read_text())
except (OSError,ValueError):state={}
try:rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'))
except OSError:rows=[]
peer={}
for path in T.parent.glob('take-*-r34/take.tsv'):
 if path.parent==T:continue
 try:
  for z in csv.DictReader(path.open(),delimiter='\t'):
   n=int(z['n']);peer[n]=min(peer.get(n,float('inf')),float(z['new']))
 except (OSError,KeyError,ValueError):pass
allrows=rows
rows=[z for z in rows if float(z['new'])<peer.get(int(z['n']),float('inf'))-1e-10]
s=dict(time=time.strftime('%FT%TZ',time.gmtime()),attempts=len(r),counts=len({x['n'] for x in r}),raw=sum(bool(x.get('raw')) for x in r),states=dict(collections.Counter(x.get('status') for x in state.values())),retained=[int(x['n']) for x in rows],gain=sum(float(x['gain']) for x in rows),errors=sum(bool(x.get('error')) for x in r))
s['source_counts']=[int(x['n']) for x in allrows]
s['source_gain']=sum(float(x['gain']) for x in allrows)
for name in ['finalize34.error','finalize34.done','guardian34-status.json']:
 p=W/name
 if p.exists():s[name]=p.read_text()[:300]
print(json.dumps(s),flush=True)
