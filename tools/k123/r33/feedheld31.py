"""Claim one untouched held start at a time in the existing scan slot."""
from pathlib import Path
import sys,time,subprocess,csv,json,hashlib,datetime,re,io
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import credit,mlp,legacy_credit
if (W/'held-intake-closed31').exists():raise SystemExit
from base25 import loadpack,paths,current
if not (W/'taskdone/verify-held31-control.json').exists():raise SystemExit
statefile=W/'held-probe-state31.json';state=json.load(statefile.open()) if statefile.exists() else {}
# One in-flight held task keeps fresh scans responsive.
active=[v['tag'] for v in state.values() if v.get('tag') and not (W/'taskdone'/(v['tag']+'.json')).exists()]
if active:raise SystemExit
if time.time()>float((W/'search-deadline').read_text())-1000:raise SystemExit
P=loadpack(paths()[0]);bars={int(r['n']):float(r['bar']) for r in csv.DictReader((S/'round33-briefs/bar33.tsv').open(),delimiter='\t')}
prior='\n'.join((S/f'handoff-r{r}.log').read_text() for r in [28,29,30]);live=(S/'handoff-r33.log').read_text()
prior_claims=set(int(n) for l in prior.splitlines() if 'kick' in l.lower() and 'claim' in l.lower() for n in re.findall(r'\bn\s*[=:]\s*(\d+)',l))
# First use the unrun border list, then rows never named in recent claims.
orders=json.load((S/'take-border-r30/work/held30/order3.json').open()) if (S/'take-border-r30/work/held30/order3.json').exists() else {}
candidates=sorted((n for n in P if n>=400 and n not in prior_claims),key=lambda n:(str(n) not in orders,-bars[n]))
SSH=['ssh','-S','/tmp/squares-k123-r33-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r33-ssh']
for n in candidates:
 if str(n) in state:continue
 A=P[n];side=mlp.side(A)
 if abs(side-round(side))<1e-8:state[str(n)]={'status':'integer grid'};continue
 D=W/'held-starts31';D.mkdir(exist_ok=True);start=D/f'{n}.csv'
 with start.open('w') as f:
  wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle']);wr.writerows((n,i,*row) for i,row in enumerate(A))
 raw=start.read_bytes();digest=hashlib.sha256(raw).hexdigest();now=time.time();claimed=False
 for l in live.splitlines():
  if 'claim' not in l.lower() or 'kick' not in l.lower():continue
  try:age=now-datetime.datetime.fromisoformat(l.split()[0].replace('Z','+00:00')).timestamp()
  except (ValueError,IndexError):continue
  if age<3600 and (digest in l or digest[:16] in l):claimed=True;break
 if claimed:state[str(n)]={'status':'claimed exact bytes'};continue
 c=credit(n,A,'held')
 if not c:state[str(n)]={'status':'source deferred'};continue
 # Plain public parents measured zero in r30 and are not useful kick starts.
 if not any(x in (legacy_credit(n,A,'held') or {}).get('source','').lower() for x in ['fq','join','step','kick','own','held','samanyu']):state[str(n)]={'status':'plain public source'};continue
 pool='held31n'+str(n)+'h'+digest[:12];tag='verify-held31-'+str(n)+'-'+digest[:12];D=W/pool;D.mkdir(exist_ok=True)
 source=f'held packing of n = {n} of round 30; gather/round30-2026-11-15c.csv; exact row snapshot {start} (sha256 {digest}); table {c.get("table","")}; {c["source"]}'
 c={**c,'source':source,'input_file_snapshot':str(start),'input_file_sha256':digest}
 (D/(pool+'.csv')).write_bytes(raw);(D/('sources-'+pool+'.json')).write_text(json.dumps({str(n):c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text())
 task={'kind':'verify','tag':tag,'held_probe31':True,'n':n,'pool':pool,'seed':310000+n,'input_sha256':digest};(D/(tag+'.json')).write_text(json.dumps(task))
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: CLAIM kick900s with120s probe n={n} sha256={digest}, held round30c row {start}; boxE existing scan slot, source {D}\n'
 with (S/'handoff-r33.log').open('a') as f:f.write(line)
 with (T/'STATE.txt').open('a') as f:f.write(line.rstrip()+'; common deadline00:15Z.\n')
 for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']:subprocess.run(SCP+[str(D/name),'boxE:scratch/squares-k123/'+name],check=True)
 subprocess.run(SCP+[str(D/(tag+'.json')),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True)
 subprocess.run(SSH+['cd $SCRATCH/squares-k123 && mv tasks/'+tag+'.json.tmp tasks/'+tag+'.json'],check=True)
 state[str(n)]={'status':'queued','tag':tag,'sha256':digest};print(line.strip(),flush=True);break
statefile.write_text(json.dumps(state,indent=2))
