"""Admit never-started raw jobs in current fit order after fresh work."""
from pathlib import Path
import sys,json,csv,shutil,hashlib,math,time
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent;O=B/'take-twoshort-r24/work';R=O/'boxE24'
sys.path.insert(0,str(W));from admit25 import store;from shape974 import load,distance
bar=json.load(open(W/'bar.json'));claims=(B/'handoff-r25.log').read_text();pending=json.load(open(O/'pending-final.json'))['jobs'];pool={};events=[];candidates=[]
for p in (R/'done').glob('*.json'):
 j=json.load(open(p));st=j.get('start','')
 if not st or not j.get('start_side'):continue
 q=R/st.split('/scratch/squares-twoshort/')[-1]
 if q.exists():
  a,s=load(q);pool.setdefault(j['n'],[]).append((a,s,str(q)))
for j in pending:
 if not j.get('start') or not j.get('n'):events.append(dict(tag=j.get('tag'),status='specification job handled separately'));continue
 if any('backlog ->' in l and 'claim' in l.lower() and j['tag'] in l for l in claims.splitlines()):events.append(dict(tag=j['tag'],status='claimed by backlog'));continue
 p=R/j['start'].split('/scratch/squares-twoshort/')[-1]
 if not p.exists():events.append(dict(tag=j['tag'],status='missing snapshot'));continue
 a,side=load(p);n=j['n'];gap=side-bar[str(n)]
 candidates.append((gap,j,p,a,side))
for gap,j,p,a,side in sorted(candidates,key=lambda t:t[0]):
 n=j['n'];tag='pending25-'+j['tag'];reason=None
 for arr,s,q in pool.get(n,[]):
  if abs(side-s)<2e-8 and distance(a,side,arr)<2e-8:reason='matches completed geometry '+q;break
 if reason:events.append(dict(tag=j['tag'],status=reason));continue
 ok,proof=store(dict(source=j['source'],licence=j['licence']),n=n)
 if not ok:events.append(dict(tag=j['tag'],status='source refused',errors=proof['closure']['errors'][:2]));continue
 name=tag+'.csv';dst=W/'starts'/name;shutil.copy2(p,dst)
 digest=hashlib.sha256(dst.read_bytes()).hexdigest();pp=W/'intake'/(tag+'-ancestry.json');pp.write_text(json.dumps(dict(admitted=True,snapshot=str(dst),sha256=digest,ancestry=proof)))
 jj={k:j[k] for k in ['n','source','licence']};jj.update(tag=tag,start='starts/'+name,seed=625,remaining=2,seconds=180,miss=0,priority=60,force_quench=False,input_ancestry_proof=str(pp))
 (W/'jobs'/('060-'+tag+'-625.json')).write_text(json.dumps(jj));pool.setdefault(n,[]).append((a,side,str(dst)));events.append(dict(tag=j['tag'],status='queued',gap=gap))
 with open(B/'handoff-r25.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> backlog: CLAIM old raw job '+j['tag']+', '+str(p)+'\n')
(W/'pending-job-admission.json').write_text(json.dumps(events,indent=2));from collections import Counter;print(Counter(x['status'].split(' matches')[0].split('geometry')[0] for x in events))
