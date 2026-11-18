"""Keep one module-family request ahead of raw copies, alongside useful raw continuations."""
from pathlib import Path
import json,time,os,sys

def atomic(p,d):
 t=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def run(R):
 events=[];done={}
 for p in (R/'done').glob('*.json'):
  d=json.load(open(p));done[(d.get('tag'),d.get('seed'))]=d
 for p in (R/'jobs').glob('005-*.json'):
  if (R/'locks'/p.name).exists():continue
  j=json.load(open(p));j['force_quench']=False;atomic(p,j);old=done.get((j.get('tag'),j.get('seed',0)-1),{})
  if old.get('start_side',0)-old.get('best',0)<=1e-6:continue
  q=R/'jobs'/('000-00-leg-'+p.name[4:]);p.rename(q);events.append(dict(kind='leg',old=p.name,new=q.name,n=j['n']))
 family=[];active=False;waiting=False
 for p in list((R/'jobs').glob('*.json')):
  j=json.load(open(p))
  if j.get('kind') not in ['design','specs'] or j.get('tag','').startswith('control'):continue
  locked=(R/'locks'/p.name).exists();finished=(R/'done'/p.name).exists()
  if locked and not finished:active=True
  if locked or finished:continue
  if p.name.startswith('000-00-family-'):waiting=True;continue
  if not p.name.startswith('040-family-'):
   q=R/'jobs'/('040-family-'+p.name);p.rename(q);(R/'locks'/p.name).mkdir(exist_ok=True);atomic(R/'done'/p.name,dict(kind='alias',target=q.name,tag=j['tag']));p=q
  lib=R/'designs'/j['tag']/'lib/library.pkl';size=lib.stat().st_size if lib.exists() else 10**12
  family.append((j.get('kind')!='design',size,-p.stat().st_mtime_ns,p,j))
 if family and not active and not waiting:
  _,_,_,p,j=min(family,key=lambda x:x[:3]);q=R/'jobs'/('000-00-family-'+p.name);p.rename(q);events.append(dict(kind='family',old=p.name,new=q.name,tag=j['tag']))
 with open(R/'priority-promotions.jsonl','a') as f:
  for d in events:f.write(json.dumps(dict(d,time=time.strftime('%FT%TZ',time.gmtime())))+'\n')
 return events
if __name__=='__main__':print(run(Path(sys.argv[1]) if len(sys.argv)>1 else Path.home()/'scratch/squares-twoshort'))
