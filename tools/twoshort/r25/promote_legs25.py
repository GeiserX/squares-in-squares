from pathlib import Path
import json,time
R=Path.home()/'scratch/squares-twoshort';events=[]
for p in (R/'jobs').glob('005-*.json'):
 if (R/'locks'/p.name).exists():continue
 j=json.load(open(p));previous=[]
 for q in (R/'done').glob('*.json'):
  d=json.load(open(q))
  if d.get('tag')==j.get('tag') and d.get('seed')==j.get('seed',0)-1 and d.get('start_side',0)-d.get('best',0)>1e-6:previous.append(d)
 if not previous:continue
 new=R/'jobs'/('000-00-leg-'+p.name[4:]);p.rename(new);events.append(dict(old=p.name,new=new.name,n=j['n']))
with open(R/'priority-promotions.jsonl','a') as f:
 for d in events:f.write(json.dumps(dict(d,time=time.strftime('%FT%TZ',time.gmtime())))+'\n')
print(events)
