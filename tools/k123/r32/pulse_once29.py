from pathlib import Path
import csv,json,time,datetime,subprocess
W=Path(__file__).resolve().parent;T=W.parent
csv.field_size_limit(1<<28)
def read(p):return p.read_text() if p.exists() else ''
records=[]
for line in read(W/'records.jsonl').splitlines():
 try:records.append(json.loads(line))
 except ValueError:pass
rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));resident=read(W/'resident25.log').splitlines();age={}
for mode in ['collect','stage']:
 l=next((l for l in reversed(resident) if f' {mode} ' in l),'')
 if l:
  stamp=datetime.datetime.strptime(l.split()[0],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp();age[mode]=round(time.time()-stamp)
print(json.dumps(dict(time=time.strftime('%H:%M:%SZ',time.gmtime()),joins=len(records),counts=len({r['n'] for r in records}),raws=sum(bool(r.get('raw')) for r in records),errors=sum(bool(r.get('error')) for r in records),takes=[int(r['n']) for r in rows],gain=sum(float(r['gain']) for r in rows),age=age,finalizer_error=read(W/'finalize26.error'),reported=(T/'report.json').exists())))
