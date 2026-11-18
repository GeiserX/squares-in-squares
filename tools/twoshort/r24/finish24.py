"""Audit the round 24 take and save the remaining exact jobs."""
from pathlib import Path
import sys,json,csv,math,shutil,datetime,subprocess
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent;T=W.parent;R=W/'boxE24';LANE=Path('.');sys.path.insert(0,str(W/'lane'));import floatsafe
write='--write' in sys.argv
sys.path.insert(0,str(W));from bar24 import bars as policy_bars,policy,reference,FP
held,held22,sam_bar,free_bar=policy_bars(T);bar=free_bar;who={}
keep=[];dropped=[]
for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(r['n']);p=T/(str(n)+'.csv');rows=[{k:r[k] for k in ['n','square_id','x','y','angle']} for r in csv.DictReader(open(p))];_,fr,s,e=floatsafe.work((n,rows));assert fr is not None and abs(s-float(r['new']))<5e-13,(n,s,r['new']);assert floatsafe.clearance(fr)>=2.2e-11
 pol=policy(r['source'],r['licence']);ref=reference(n,pol,held,held22);livebar=free_bar[n] if pol['status']=='none' else sam_bar[n]
 if s>=ref-1e-10 or s>=livebar-1e-10:
  dropped.append(dict(n=n,score=s,winner=who.get(n,'candidate'),bar=livebar))
  if write:shutil.copy2(p,T/'near'/(str(n)+'-superseded-final.csv'));(T/'near'/(str(n)+'-superseded-final.json')).write_text(json.dumps(dict(r,reason='superseded'),indent=2));p.unlink()
 else:keep.append(r)
if write:
 with (T/'take.tsv.tmp').open('w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(keep)
 (T/'take.tsv.tmp').replace(T/'take.tsv')
done=[json.load(open(p)) for p in R.glob('done/*.json')];kicks=[d for d in done if 'tries' in d and not d.get('tag','').startswith('control')];completed={(d.get('tag'),d.get('seed')) for d in done if d.get('seed') is not None};pending=[];aliases=[]
for p in R.glob('jobs/*.json'):
 if (R/'locks'/p.name).exists():continue
 j=json.load(open(p))
 if (j.get('tag'),j.get('seed')) in completed:aliases.append(p.name);continue
 pending.append(j)
partial=[]
for p in R.glob('designs/*/unstarted.json'):
 rows=json.load(open(p))
 if rows:partial.append(dict(path=str(p),rows=rows))
builds=[json.load(open(p)) for p in R.glob('designs/*/builds/*.json') if not p.parent.parent.name.startswith('control')];screens=[json.load(open(p)) for p in R.glob('designs/library-*/summary.json')]
stats=dict(at=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ'),improved_n=len(keep),gain=dict(round23_candidate=sum(held[int(r['n'])]-float(r['new']) for r in keep),other_live_r24=sum((free_bar if policy(r['source'],r['licence'])['status']=='none' else sam_bar)[int(r['n'])]-float(r['new']) for r in keep)),rows=keep,dropped=dropped,kick_scans=len(kicks),tries=sum(d['tries'] for d in kicks),builds=len(builds),screens=len(screens),completed_quenches=sum(json.load(open(p)).get('quench_rc')==0 for p in R.glob('q/*/meta.json')),pending_jobs=len(pending),partial_batches=len(partial),partial_specifications=sum(len(d['rows']) for d in partial))
if any(int(r['n']) in FP.RELAXED and policy(r['source'],r['licence'])['status']=='none' for r in keep):stats['gain']['policy_reference']=sum(reference(int(r['n']),policy(r['source'],r['licence']),held,held22)-float(r['new']) for r in keep)
(W/'final-stats.json').write_text(json.dumps(stats,indent=2));(W/'pending-final.json').write_text(json.dumps(dict(jobs=pending,partial=partial,ignored_aliases=aliases),indent=2))
subprocess.run([str(B/'venv/bin/python'),str(W/'results24.py'),str(LANE/'results/twoshort-r24-2026-11-13.tsv') if write else str(W/'results-current.tsv')],check=True)
print(json.dumps({k:v for k,v in stats.items() if k!='rows'},indent=2))
