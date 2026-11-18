from pathlib import Path
import csv,json,collections,datetime
W=Path(__file__).parent;R=W/'boxE26';done=[]
for p in (R/'done').glob('*.json'):
 try:done.append(json.load(open(p)))
 except ValueError:pass
k=[d for d in done if 'tries' in d and not d.get('tag','').startswith('control')];builds=[]
for p in R.glob('designs/*/builds/*.json'):
 if not p.parent.parent.name.startswith('control'):
  d=json.load(open(p));builds.append((d,p))
q=list(R.glob('q/*/meta.json'));best=sorted([(d['built']-d['held'],d['n'],str(p)) for d,p in builds if d.get('built') is not None])[:5]
take=list(csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t'));print(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),done=len(done),kicks=len(k),tries=sum(d['tries'] for d in k),builds=len(builds),quenches=len(q),take=[r['n'] for r in take],near=best),indent=2))
